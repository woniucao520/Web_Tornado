import os.path
import json
import yaml

import tornado
from tornado import escape, gen, httpserver, ioloop, web, websocket

from sqlalchemy.exc import IntegrityError,DBAPIError

from ORM import Session
from ORM.Tables.User import User
from ORM.Tables.UserBank import UserBank
from ORM.Tables.OrderSub import OrderSub
from ORM.Tables.UserWithdraw import UserWithdraw
from ORM.Tables.Product import Product

import Common
from Commands.Command import Command
from Commands.UserHandler import UserHandler
from Commands.ProductHandler import ProductHandler
from Commands.OrderHandler import OrderHandler
from Commands.OrderDealHandler import OrderDealHandler

import logging
import logging.config

import redis
import math, operator, time

from Configuration import ConfigParser


class Application(tornado.web.Application):

    def __init__(self):

        logging.config.dictConfig(yaml.load(open(os.path.realpath('log.yaml'), 'r')))
        logging.getLogger('sqlalchemy.engine').setLevel(logging.DEBUG)
        logging.getLogger('sqlalchemy.pool').setLevel(logging.WARN)


        handlers = [
            (r"/", HomeHandler),
            # 增加 demo，
            (r"/user/ajax_login",UserAjaxLogin),
            #用户注册
            (r"/url/numregisted",UserNumRegisted),
            #忘记密码
            (r"/url/forget_password",UserForgetPassword),
            # 发送验证码
            (r"/url/sendcode",UserSendCodeHandler),
            #找回密码的验证
            (r"/url/identity_check",UserIdentityCheck),

            (r"/user/create", UserCreateHandler),
            (r"/user/login", UserLoginHandler),
            (r"/user/logout", UserLogoutHandler),
            (r"/user/console", UserConsoleHandler),
            (r"/user/profile", UserProfileHandler),
            (r"/user/update", UserUpdateHandler),
            (r"/user/wallet", UserWalletHandler),
            (r"/user/withdraw", UserWithdrawHandler),
            (r"/user/withdraw-history", UserWithdrawHistoryHandler),
            (r"/user/deposit-history", UserDepositHistoryHandler),
            (r"/user/subbuy", UserSubBuyHandler),
            (r"/user/buy", UserBuyHandler),
            (r"/user/sale", UserSaleHandler),
            (r"/user/orders", UserOrdersHandler),
            (r"/transaction", TransactionSocketHandler),
            (r"/product/list", ProductListHandler),
            (r"/product/detail", ProductDetailHandler),
            (r"/product/buy", ProductBuyHandler),
            (r"/product/sale", ProductSaleHandler),
            (r"/product/order", ProductOrderHandler),
            (r"/product/assets", ProductAssetsHandler),
            (r"/order/cancel", OrderCancelHandler),
            (r"/bank/create", BankCreateHandler),
            (r"/api/transaction/products", TransactionProductsHandler)
        ]

        settings = dict(
            site_title=u"吾品玉艺玉文化产权拍卖服务平台",
            template_path=os.path.join(os.path.dirname(__file__), "WWW/templates"),
            static_path=os.path.join(os.path.dirname(__file__), "WWW/static"),
            #ui_modules={"Entry": EntryModule},
            xsrf_cookie=True,
            cookie_secret="xxddfewr44343gfd32dsf3ds22d",
            debug=True,
        )

        super(Application, self).__init__(handlers, **settings)

        self.session = Session()

        try:
            self.redis = redis.StrictRedis(ConfigParser.get('wx.redis.config','host'),ConfigParser.get('wx.redis.config','port'))

        except redis.ConnectionError as e:
            logging.warning(e.args[0])
            exit(0)
        else:
            logging.info('Connected to the redis:{}....'.format(self.redis))



class BaseHandler(tornado.web.RequestHandler):   # BHandler，可以自定义采用的模板，所有的handler都继承这个类

    @property
    def session(self):
        return self.application.session

    @property
    def redis(self):
        return self.application.redis
# 验证用户登录状态 user_id
    def get_current_user(self):
        user_id = self.get_secure_cookie("wx_user_id")
        if not user_id:
            return None

        #TODO only return the user object and need sub class to check user status
        try:
            user = self.session.query(User).get(user_id)
        except DBAPIError as e :
            self.session.rollback()
            if e.connection_invalidated:
                logging.warning('database connection invalid')
        finally:
            self.session.close()

        if not user:
            user = self.session.query(User).get(user_id)

        return user

class HomeHandler(BaseHandler):

    def get(self):
        referrer = self.get_query_argument('referrer',0)
        self.set_secure_cookie('referrer_id', str(referrer))

        self.render("home.html",referrer=referrer)

class UserCreateHandler(BaseHandler):

    def get(self):
        self.render("user/create.html", referrer_id=self.get_secure_cookie('referrer_id'))

    def post(self):
        user = User()
        user.login_name = self.get_argument('login_name')
        user.login_pass = User.encrypt_pass(self.get_argument('login_pass'))
        user.real_name = self.get_argument('realname')
        user.id_no = self.get_argument('id_no')
        user.mobile = self.get_argument('mobile')

        if self.get_argument('display_name',None):
            user.display_name = self.get_argument('display_name')
        else:
            user.display_name = user.login_name

        user.status = User.UserStatusPending

        user.referrer_id = self.get_argument('referrer', 0)

        if UserHandler.checkIdNo(user.id_no):
            data = {'result': 'error', 'msg': '身份证号码已被注册！'}
            self.write(json.JSONEncoder().encode(data))
            return

        try:
            self.session.add(user)
            self.session.commit()

            data = {'result': 'success', 'msg': user.id}
            self.write(json.JSONEncoder().encode(data))
        except IntegrityError as e:
            self.session.close()
            if 'login_name' in e.args[0]:
                msg =  self.get_argument('login_name') + ' 已经被注册!'
            elif 'mobile' in e.args[0]:
                msg = self.get_argument('mobile') + ' 已经被注册!'
            else:
                msg = '未知错误,请联系平台处理'

            data = {'result':'error', 'msg':msg}
            self.write(json.JSONEncoder().encode(data))

        except DBAPIError as e:
            if e.connection_invalidated:
                logging.warning('database connection invalid')

                data = {'result': 'error', 'msg': 'database connection invalid'}
                self.write(json.JSONEncoder().encode(data))
        except Exception as e:
            print(e.args[0])

        finally:
            self.session.close()



class UserNumRegisted(BaseHandler):
    # 判断用户是否注册，yes:跳转到登录页面
    def get(self):
        self.render("user/login.html",error=None)
    def post(self):
        pass

   # no，注册


# 用户忘记密码
class UserForgetPassword(BaseHandler):

    def get(self):
        self.render("user/forget_password.html", error=None)


# 发送验证码：调用第三方接口，获取用户的手机号码，发送验证码
class UserSendCodeHandler(BaseHandler):

    def post(self):
        mobile = self.get_argument('mobile')
        data = {}
        data['result'] = 'success'
        data['code'] = '2222'
        self.write(json.JSONEncoder().encode(data))




# 提交验证：验证码以及密码
class UserIdentityCheck(BaseHandler):

    def post(self):
        # user = User()
        mobile = self.get_argument('mobile')
        code = self.get_argument('code')

        # 这是在后端进行验证
        if code == '123456':
            newpassword = self.get_argument('newpassword')
            confirmnewpassword = self.get_argument('confirmnewpassword')
            if newpassword == confirmnewpassword and len(newpassword)>0:
            # 数据库密码更新的操作
                msg = '恭喜，密码设置成功'
                data = {'result':'success','msg':msg}

            elif newpassword != confirmnewpassword:
                msg = '抱歉，两次密码输入不正确'
                data = {'result':'error','msg':msg}
            else:
                msg ='密码不能为空'
                data = {'result': 'error', 'msg': msg}
            self.write(json.JSONEncoder().encode(data)) # 不需要每个else里都写一遍。
        else:
            msg = "您输入的验证码不正确"
            data = {'result':'error','msg':msg}
            self.write(json.JSONEncoder().encode(data))


class UserLoginHandler(BaseHandler):

    def get(self):
        if self.get_current_user():
            self.redirect("/user/profile")   # self.redirect 多数情况下被用于用户自定义的情况下进行重定向操作（例如环境变更、用户认证、以及表单提交）
        else:
            self.render("user/login.html", error=None)

    @gen.coroutine
    def post(self):

        login_name = self.get_argument('login_name')
        login_pass = self.get_argument('login_pass')

        user = UserHandler.login(login_name, login_pass)

        if not user:
            data = {'result': 'error', 'msg':'用户名或密码错误'}
        else:
            if operator.eq(user.status, User.UserStatusFrozen):
                data = {'result': 'error', 'msg': '当前用户:{},已被冻结，请联系平台了解详情！'.format(user.login_name)}
            elif operator.eq(user.status, User.UserStatusBlack):
                data = {'result': 'error', 'msg': '当前用户:{},已被拉黑，已无权再登录！'.format(user.login_name)}
            else:
                data = {'result': 'success', 'msg':user.id}

        self.write(json.JSONEncoder().encode(data))


class UserAjaxLogin(BaseHandler):

    @gen.coroutine
    def post(self):
        ajax_login_name= self.get_argument("login_name")
        ajax_login_pass= self.get_argument("login_pass")

        user = UserHandler.login( ajax_login_name,ajax_login_pass)

    # 判断：用户是否存在
        if not user:
            data ={'result': 'error','msg':'该用户不存在'}
        else:
            data ={'result':'successful','msg':user.id}

        self.write(json.JSONEncoder().encode(data))


class UserLogoutHandler(BaseHandler):
    def get(self):
        self.clear_cookie("wx_user_id")
        self.clear_cookie("wx_user_status")
        self.redirect(self.get_argument("next", "/"))


class UserConsoleHandler(BaseHandler):
    def post(self):
        user_id = self.get_argument('user_id', None)   # None为默认值
        if not user_id:
            self.render('error.html', message='参数缺失!')
            return

        try:
            user = self.session.query(User).filter(User.deleted == 0, User.id == user_id).one_or_none()
        except DBAPIError as e:
            logging.warning(e.args[0])
            self.render('error.html', message='Error to query user')
        else:
            if user:
                suns = UserHandler.get_suns(user_id, 1)
                self.render('user/console.html', user=user, suns=suns)
            else:
                self.render('error.html', message='Unauthorized access')


class UserProfileHandler(BaseHandler):
    def get(self):
        pass

    def post(self):
        user_id = self.get_argument('user_id', None)
        if not user_id:
            self.render('error.html', message='参数缺失!')
            return

        try:
            user = self.session.query(User).filter(User.deleted==0,User.id==user_id).one_or_none()
            user_bank = self.session.query(UserBank.bank_no,UserBank.bank_account_name, UserBank.bank_province,UserBank.bank_city ,UserBank.bank_name,UserBank.bank_branch_name).filter(UserBank.deleted==0,UserBank.user_id==user_id).order_by(UserBank.is_default.desc()).all()
        except DBAPIError as e:
            logging.warning(e.args[0])
            self.render('error.html', message='Error to query user')
        else:
            if user:
                self.render('user/profile.html', user=user, banks=user_bank)
            else:
                self.render('error.html', message='Unauthorized access')


class UserUpdateHandler(BaseHandler):
    def post(self):
        user_id = self.get_argument('user_id')
        col = self.get_argument('flag')
        value = self.get_argument('value')


        try:
            self.session.query(User).filter(User.id == user_id).update({col:value})
            self.session.commit()
        except DBAPIError as e:
            self.session.rollback()
            data = {'result':'error','msg':e.args[0]}
            self.write(json.JSONEncoder().encode(data))
        else:
            data = {'result': 'success', 'msg': 'okay'}
            self.write(json.JSONEncoder().encode(data))
        finally:
            self.session.close()

class UserWalletHandler(BaseHandler):
    def post(self):
        login_name = self.get_argument('username', None)
        user_id = self.get_argument('user_id', None)

        if not login_name or not user_id:
            self.render("error.html", message="Bad Request")
            return

        money_info = {}
        avaliable_money = UserHandler.get_available_money(user_id)
        in_using_money = UserHandler.get_in_using_money(user_id)
        can_used_money = round((avaliable_money-in_using_money), 2)
        frozen_money = UserHandler.get_frozen_money(user_id)
        money_info['am'] = avaliable_money
        money_info['cum'] = can_used_money
        money_info['fm'] = frozen_money

        total_assets = UserHandler.get_total_assets_amount(user_id)

        assets_info = UserHandler.get_assets(user_id)

        self.render("user/wallet.html", total_assets=total_assets, money_info=money_info, assets_info=assets_info)


class UserOrdersHandler(BaseHandler):

    def post(self):
        login_name = self.get_argument('username', None)
        user_id = self.get_argument('user_id', None)

        if not login_name or not user_id:
            self.render("error.html", message="参数缺失!")
            return

        sub_info = Common.get_user_subscription(session=self.session, user_id=user_id)

        self.render("user/orders.html", sub_info=sub_info)

class UserSubBuyHandler(BaseHandler):
    def post(self):
        user_id = self.get_argument('user_id', None)
        qty = self.get_argument('qty', None)
        price = self.get_argument('price', None)
        p_no = self.get_argument('p_no', None)

        if not user_id or not qty or not price or not p_no:
            data = {'result': 'error', 'msg': '参数缺失!'}
            self.write(json.JSONEncoder().encode(data))
            return

        total_assets = UserHandler.get_total_assets_amount(user_id)

        max_qty = 0.2  #g

        if operator.eq(total_assets, 0):
            max_qty = 0.2
            if operator.gt(float(qty), max_qty):
                data = {'result': 'error', 'msg': '新用户最多可认购：{}克!'.format(max_qty)}
                self.write(json.JSONEncoder().encode(data))
                return
        else:
            if total_assets >=10000:
                max_qty = 0.4
            elif total_assets >=1000:
                max_qty = 0.2
            else:
                max_qty = 0

            if operator.gt(float(qty), max_qty):
                data = {'result': 'error', 'msg': '您总持仓为：{}元，最多可认购：{}克!'.format(total_assets, max_qty)}
                self.write(json.JSONEncoder().encode(data))
                return


        try:
            order_sub = OrderSub()
            order_sub.user_id = user_id
            order_sub.p_no  = 'CZQH'
            order_sub.qty = float(qty)*100
            order_sub.price = float(price)/100.00
            order_sub.amount = float(qty) * float(price)
            order_sub.status = OrderSub.StatusWaitForPaid
            order_sub.unit = 'h'
            order_sub.created_at = time.time()

            self.session.add(order_sub)
            self.session.commit()
        except DBAPIError as e:
            self.session.rollback()
            logging.warning(e.args[0])
            if e.connection_invalidated:
                logging.warning('database connection invalid')

            data = {'result': 'error', 'msg': '未知错误,请联系平台处理'}
            self.write(json.JSONEncoder().encode(data))
        else:
            data = {'result': 'success', 'msg': order_sub.id}
            self.write(json.JSONEncoder().encode(data))
        finally:
            self.session.close()

class UserWithdrawHandler(BaseHandler):
    def get(self):
        user_id = self.get_argument('user_id', None)

        max_amount = UserHandler.get_can_withdraw_money(user_id)
        banks = UserHandler.get_banks(user_id)

        self.render('user/withdraw.html', max_amount=max_amount, banks=banks)

    def post(self):
        user_id = self.get_argument('user_id', None)
        bank_id = self.get_argument('bank_id', None)
        amount = self.get_argument('amount', None)

        if not user_id or not bank_id or not amount:
            data = {'result': 'error', 'msg': '参数缺失!'}
            self.write(json.JSONEncoder().encode(data))
            return

        maxValue = UserHandler.get_can_withdraw_money(user_id)
        if operator.gt(float(amount), float(maxValue)):
            data = {'result': 'error', 'msg': '提现金额不得大于:{}'.format(maxValue)}
            self.write(json.JSONEncoder().encode(data))
            return

        uw = UserWithdraw()
        uw.user_id = user_id
        uw.bank_id = bank_id
        uw.amount = amount
        uw.status = UserWithdraw.StatusPending

        self.session.add(uw)

        try:
            self.session.commit()
        except DBAPIError as e:
            print(e.args[0])
            data = {'result': 'error', 'msg': '提现申请失败，请稍后尝试!'}
        else:
            data = {'result': 'success', 'msg': 'successfully!'}
        finally:
            self.session.close()


        self.write(json.JSONEncoder().encode(data))


class UserWithdrawHistoryHandler(BaseHandler):
    def post(self):
        user_id = self.get_argument('user_id', None)

        if not user_id:
            data = {'result': 'error', 'msg': '参数缺失!'}
            self.write(json.JSONEncoder().encode(data))
            return

        records = UserHandler.get_withdraw_history(user_id)

        self.render('user/withdraw-history.html', histories=records)

class UserDepositHistoryHandler(BaseHandler):
    def post(self):
        user_id = self.get_argument('user_id', None)

        if not user_id:
            data = {'result': 'error', 'msg': '参数缺失!'}
            self.write(json.JSONEncoder().encode(data))
            return

        records = UserHandler.get_deposit_history(user_id)

        self.render('user/deposit-history.html', histories=records)

class UserBuyHandler(BaseHandler):
    def post(self):
        p_no = self.get_argument('p_no', None)
        user_id = self.get_argument('user_id', None)
        price = self.get_argument('price', None)
        qty = self.get_argument('qty', None)

        if not p_no or not user_id or not price or not qty:
            data = {'result': 'error', 'msg': '参数缺失!'}
            self.write(json.JSONEncoder().encode(data))
            return

        result,message = OrderHandler.insert_buy_order(user_id,p_no,qty,price)

        if not result:
            data = {'result': 'error', 'msg': message}
        else:
            self.redis.publish(ConfigParser.get('wx.redis.config','channels')['matching'],json.JSONEncoder().encode({'P_NO':p_no}))
            data = {'result': 'success', 'msg': '委托成功!'}

        self.write(json.JSONEncoder().encode(data))


class UserSaleHandler(BaseHandler):
    def post(self):
        p_no = self.get_argument('p_no', None)
        user_id = self.get_argument('user_id', None)
        price = self.get_argument('price', None)
        qty = self.get_argument('qty', None)

        if not p_no or not user_id or not price or not qty:
            data = {'result': 'error', 'msg': '参数缺失!'}
            self.write(json.JSONEncoder().encode(data))
            return

        result,message = OrderHandler.insert_sale_order(user_id,p_no,qty,price)

        if not result:
            data = {'result': 'error', 'msg': message}
        else:
            self.redis.publish(ConfigParser.get('wx.redis.config','channels')['matching'], json.JSONEncoder().encode({'P_NO': p_no}))
            data = {'result': 'success', 'msg': '委托成功!'}

        self.write(json.JSONEncoder().encode(data))

class BankCreateHandler(BaseHandler):
    def post(self):
        user_id = self.get_argument('user_id', None)
        bank_no = self.get_argument('bank_no', None)
        bank_account_name = self.get_argument('bank_account_name', None)
        bank_province = self.get_argument('bank_province', None)
        bank_city = self.get_argument('bank_city', None)
        bank_name = self.get_argument('bank_name', None)
        bank_branch_name = self.get_argument('bank_branch_name', None)
        is_default = self.get_argument('is_default', 0)

        if not user_id or \
                not bank_no or \
                not bank_account_name or \
                not bank_province or \
                not bank_city or \
                not bank_name or \
                not bank_branch_name:
            data = {'result': 'error', 'msg': '参数缺失!'}
            self.write(json.JSONEncoder().encode(data))
            return

        ub = UserBank()
        ub.user_id = user_id
        ub.bank_no = bank_no
        ub.bank_account_name = bank_account_name
        ub.bank_province = bank_province
        ub.bank_city = bank_city
        ub.bank_name = bank_name
        ub.bank_branch_name = bank_branch_name
        ub.is_default = is_default

        try:
            self.session.add(ub)
            self.session.commit()
        except DBAPIError as e:
            print(e.args[0])
            data = {'result': 'error', 'msg': 'Error to save!'}
        else:
            data = {'result': 'success', 'msg': 'successfully!'}
        finally:
            self.session.close()

        self.write(json.JSONEncoder().encode(data))


class EntryModule(tornado.web.UIModule):

    def render(self, entry):
        return self.render_string("modules/entry.html", entry=entry)


class ProductListHandler(BaseHandler):

    def post(self):

        data = ProductHandler.get_app_products_list()

        self.render("product/list.html", data=data)

class ProductDetailHandler(BaseHandler):
    def post(self):
        p_no = self.get_argument('p_no',None)
        if not p_no:
            self.render('error.html', message='Product no is empty')

        segment = self.get_argument('segment', None)

        if not segment:
            info = ProductHandler.get_app_product_info(p_no)

            x_times = ProductHandler.get_transaction_times(p_no)
            d_price = []
            a_price = []
            d_volume = []

            data = OrderDealHandler.get_deal_data(p_no)

            for t, dp, ap, dv in data:
                #x_times.append(t)
                d_price.append(dp)
                a_price.append(ap)
                d_volume.append(dv)
            bIndex = ['一', '二', '三', '四', '五']
            sale_5 = Common.get_top_5_delegate_sale_orders(self.session, p_no) #Common.get_lastest_5_delegate_orders(self.session, p_no, 'S')

            buy_5 = Common.get_top_5_delegate_buy_orders(self.session, p_no) #Common.get_lastest_5_delegate_orders(self.session, p_no, 'B')

            kdata = Common.get_k_data(self.session,p_no)

            self.render('product/detail.html', info=info, x=x_times, dp=d_price,ap=a_price,dv=d_volume, bi=bIndex, sd5=sale_5, bd5=buy_5, kd=kdata)
        else:
            if operator.eq(segment,'general'):
                info = ProductHandler.get_app_product_info(p_no)

                self.render('product/detail-general.html', info=info)
            elif operator.eq(segment, 'chart-time'):
                x_times = []
                d_price = []
                a_price = []
                d_volume = []

                data = OrderDealHandler.get_deal_data(p_no)

                for t, dp, ap, dv in data:
                    x_times.append(t)
                    d_price.append(dp)
                    a_price.append(ap)
                    d_volume.append(dv)

                kdata = Common.get_k_data(self.session, p_no)

                data = {'xt':x_times,'dp':d_price,'ap':a_price,'dv':d_volume}

                self.write(json.JSONEncoder().encode(data))
            elif operator.eq(segment, 'chart-k'):
                kdata = Common.get_k_data(self.session, p_no)

                self.write(json.JSONEncoder().encode(kdata))
            elif operator.eq(segment, 'bs5'):
                bIndex = ['一', '二', '三', '四', '五']
                sale_5 = Common.get_top_5_delegate_sale_orders(self.session, p_no)
                buy_5 = Common.get_top_5_delegate_buy_orders(self.session, p_no)

                self.render('product/detail-bs5.html', bi=bIndex, sd5=sale_5, bd5=buy_5)
            elif operator.eq(segment, 'info'):
                self.render('product/detail-info.html')

class ProductBuyHandler(BaseHandler):
    def post(self):
        p_no = self.get_argument('p_no', None)
        user_id = self.get_argument('user_id', None)
        if not p_no or not user_id:
            self.render('error.html', message='Product no or user id is empty')

        pinfo = ProductHandler.get_app_product_info(p_no)#contain current_price
        can_used_money = UserHandler.get_can_used_money(user_id)
        current_price = ProductHandler.get_current_price(p_no)
        max_buy_volume = math.floor(float(can_used_money)/float(current_price))
        up_stop_price = ProductHandler.get_up_stop_price(p_no)
        down_stop_price = ProductHandler.get_down_stop_price(p_no)

        bIndex = ['一', '二', '三', '四', '五']
        sale_5 = Common.get_top_5_delegate_sale_orders(self.session,
                                                       p_no)  # Common.get_lastest_5_delegate_orders(self.session, p_no, 'S')

        buy_5 = Common.get_top_5_delegate_buy_orders(self.session,
                                                     p_no)  # Common.get_lastest_5_delegate_orders(self.session, p_no, 'B')
        #print(buy_5)
        #if buy_5 and len(buy_5)>0:
        #    buy_5.reverse()


        self.render('product/buy.html', info=pinfo, cum=can_used_money,cp=current_price,mbv=max_buy_volume, usp=up_stop_price, dsp=down_stop_price,bi=bIndex, sd5=sale_5, bd5=buy_5)

class ProductSaleHandler(BaseHandler):
    def post(self):
        p_no = self.get_argument('p_no', None)
        user_id = self.get_argument('user_id', None)
        if not p_no or not user_id:
            self.render('error.html', message='Product no or user id is empty')

        pinfo = ProductHandler.get_app_product_info(p_no)
        can_sold_product = UserHandler.get_can_sale_asset_volume(user_id, p_no)
        current_price = ProductHandler.get_current_price(p_no)
        up_stop_price = ProductHandler.get_up_stop_price(p_no)
        down_stop_price = ProductHandler.get_down_stop_price(p_no)

        bIndex = ['一', '二', '三', '四', '五']
        sale_5 = Common.get_top_5_delegate_sale_orders(self.session,
                                                       p_no)  # Common.get_lastest_5_delegate_orders(self.session, p_no, 'S')

        buy_5 = Common.get_top_5_delegate_buy_orders(self.session,
                                                     p_no)  # Common.get_lastest_5_delegate_orders(self.session, p_no, 'B')

        self.session.close()
        #if buy_5 and len(buy_5)>0:
        #    buy_5.reverse()

        self.render('product/sale.html', info=pinfo, csp=can_sold_product, cp=current_price,
                    usp=up_stop_price, dsp=down_stop_price, bi=bIndex, sd5=sale_5, bd5=buy_5)


class ProductOrderHandler(BaseHandler):
    def post(self):

        user_id = self.get_argument('user_id',None)
        if not user_id:
            self.render('error.html',message='参数错误!')
            return
        records = OrderHandler.get_my_delegates(user_id)
        self.render('product/order.html', os=records)

class ProductAssetsHandler(BaseHandler):
    def post(self):
        user_id = self.get_argument('user_id', None)

        if not user_id:
            self.render('error.html', message='参数错误!')
            return

        assets = UserHandler.get_assets(user_id)
        self.render('product/assets.html', assets=assets)

class OrderCancelHandler(BaseHandler):
    def post(self):
        user_id = self.get_argument('user_id', None)
        order_id = self.get_argument('oid', None)

        if not user_id or not order_id:
            self.render('error.html',message='参数错误!')
            return

        result, message, p_no = OrderHandler.do_cancel(user_id, order_id)
        if not result:
            data = {'result': 'error', 'msg': message}
        else:
            self.redis.publish(ConfigParser.get('wx.redis.config', 'channels')['matching'],
                               json.JSONEncoder().encode({'P_NO': p_no}))
            data = {'result': 'success', 'msg': '撤销成功!'}

        self.write(json.JSONEncoder().encode(data))

class TransactionSocketHandler(tornado.websocket.WebSocketHandler):

    waiters = set()

    @property
    def redis(self):
        return self.application.redis

    def open(self):
        TransactionSocketHandler.waiters.add(self)

    def on_close(self):
        TransactionSocketHandler.waiters.remove(self)

    @classmethod
    def broadcast(cls, msg):
        logging.info('Sending message to %d waiters', len(cls.waiters))
        for waiter in cls.waiters:
            try:
                waiter.write_message(msg)
            except:
                logging.error("Error sending message",  exc_info=True)

    def send_response(self, response):
        try:
            self.write_message(response)
        except:
            logging.error('Error to send message:{}'.format(response), exc_info=True)

    def on_message(self, message):
        logging.info('Get message %r', message)

        #TODO process get messsage

        response = Command.process_websoket_command(message, self.redis)

        response_msg = response
        #TransactionSocketHandler.send_updates(response_msg)
        #response_msg = Command.process(tornado.escape.json_decode(message), self.application.redis)

        self.send_response(response_msg)


class TransactionProductsHandler(BaseHandler):

    def post(self):
        try:
            products = self.session.query(Product).all()
        except DBAPIError as e :
            self.session.rollback()
            if e.connection_invalidated:
                logging.warning('database connection invalid')
        finally:
            self.session.close()

        result = []
        for product in products:
            result.append(product.as_dict())
        self.write(json.JSONEncoder().encode(result))
        return


def main():
    http_server = tornado.httpserver.HTTPServer(Application())
    http_server.listen(ConfigParser.get('wx.web.server.config', 'port'))
    ioloop.IOLoop.current().start()


if __name__ == '__main__':
    main()