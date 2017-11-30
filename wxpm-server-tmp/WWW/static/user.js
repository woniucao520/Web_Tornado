window.fn.User = {}

window.fn.User.register = function(){
    var username = $('#user-create #username').val();
    var password = $('#user-create #password').val();
    var confirm_pass = $('#user-create #confirm-password').val();
    var realname = $('#user-create #realname').val();
    var mobile = $('#user-create #mobile').val();
    var id_no = $('#user-create #id_no').val();
    var referrer = $('#user-create #referrer').val().trim();    //这个字段的作用是什么？

    var rname = /^[A-Za-z0-9]{6,16}$/

    if(!rname.test(username)){
        ons.notification.alert('用户名只允许使用字母或数字(6~16位)');
        return;
    }

    if(username.length < 6){
        ons.notification.alert('用户名不得少于6个字符');
        return;
    }

    if(confirm_pass !== password){
        ons.notification.alert('两次输入的密码不一致');
        return;
    }

    if(password.length <6){
        ons.notification.alert('密码至少需要6个字符');
        return;
    }

    if(realname.length <2){
        ons.notification.alert('请正确输入真实姓名');
        return;
    }

    var ridno=/^[1-9]{1}[0-9]{14}$|^[1-9]{1}[0-9]{16}([0-9]|[xX])$/;
    if(!ridno.test(id_no)){
        ons.notification.alert('身份证号格式有误');
        return;
    }

    var reg = /^1[0-9]{10}$/;
    if(!reg.test(mobile)){
        ons.notification.alert('手机格式有误');
        return;
    }

    $.ajax({
        method:'post',
        url:'/user/create',
        data:{
            login_name:username,
            login_pass:password,
            realname:realname,
            mobile:mobile,
            id_no:id_no,
            referrer:referrer
            },
        dataType:'json'

    }).done(function(data){
        if(data.result == 'error'){
            ons.notification.alert(data.msg);
        }else{
            ons.notification.toast({message: 'Welcome ' + username, timeout: 1500}).then(function(){
                localStorage.setItem('wx-user-name',username);
                localStorage.setItem('wx-user-id',data.msg);
                localStorage.setItem('wx-user-profile',realname+'|'+mobile+'|'+id_no);

                fn.load('home.html');
            });

        }

    });

}

//验证用户注册的基本信息。
window.fn.User.numregister = function () {
    var username = $('#user-create #username').val();
    var password = $('#user-create #password').val();
    var confirm_password = $('#user-create #confirm-password').val();
    var id_no = $('#user-create #id_no').val();
    var moblie = $('#user-create #mobile').val();

    var rname = /^[A-Za-z0-9]{6,16}$/

    if(!rname.test(username)){
        ons.notification.alert('用户名只允许使用字母或数字(6~16位)');
        return;
    }

    if(username.length < 6){
        ons.notification.alert('用户名不得少于6个字符');
        return;
    }

    if(confirm_pass !== password){
        ons.notification.alert('两次输入的密码不一致');
        return;
    }

    if(password.length <6){
        ons.notification.alert('密码至少需要6个字符');
        return;
    }

    if(realname.length <2){
        ons.notification.alert('请正确输入真实姓名');
        return;
    }

    var ridno=/^[1-9]{1}[0-9]{14}$|^[1-9]{1}[0-9]{16}([0-9]|[xX])$/;
    if(!ridno.test(id_no)){
        ons.notification.alert('身份证号格式有误');
        return;
    }

    var reg = /^1[0-9]{10}$/;
    if(!reg.test(mobile)){
        ons.notification.alert('手机格式有误');
        return;
    }

    $.ajax({
        method:'post',
        url:'/user/create',
        data:{
            login_name:username,
            login_pass:password,
            realname:realname,
            mobile:mobile,
            id_no:id_no,
            referrer:referrer
            },
        dataType:'json'

    }).done(function(data){
        if(data.result == 'error'){
            ons.notification.alert(data.msg);
        }else{
            ons.notification.toast({message: 'Welcome ' + username, timeout: 1500}).then(function(){
                localStorage.setItem('wx-user-name',username);
                localStorage.setItem('wx-user-id',data.msg);
                localStorage.setItem('wx-user-profile',realname+'|'+mobile+'|'+id_no);

                fn.load('home.html');
            });

        }

    });
}



window.fn.User.login = function(){
    var username = $('#user-login #username').val()
    var password = $('#user-login #password').val()

    $.ajax({
        method: 'post',
        url:'/user/login',
        data: {login_name: username,login_pass: password},
        dataType:'json'
    }).done(function(data){
        if(data.result == 'success'){
            localStorage.setItem('wx-user-name',username);
            localStorage.setItem('wx-user-id',data.msg);

            fn.load('profile.html');
        }else{
            ons.notification.alert(data.msg).then(function(){
                fn.User.clear()
            })
        }
    });

}

//忘记密码

window.fn.forget_password = function () {
    $.ajax(
        {
            method:'get',
            url:'user/forget_password',
            dataType:'html',
        }
    ).done(function (data) {
        $(target).html(data);
    });
    
}

//发送验证码

window.fn.User.sendcode = function () {
    var mobile = $('#forget-password #mobile').val()

    $.ajax({
        method : 'post',
        url :'/url/sendcode',
        data:{mobile: mobile},
        dataType:'json',
        }
    ).done(function (data) {

       if (data.result=='success'){
             ons.notification.alert("稍等,正在发送~~~~")
       }
        else{
           ons.notification.alert("未知错误，请联系平台~~~")
       }
    });

}
//提交按钮的验证：验证码，以及密码

window.fn.User.identity_check = function () {

    var mobile = $('#forget-password #mobile').val()
    var code = $('#forget-password #code').val()
    var newpassword = $('#forget-password #newpassword').val()
    var confirmnewpassword = $('#forget-password #confirmnewpassword').val()

    alert(newpassword)

    var reg = /^1[0-9]{10}$/;
    if(!reg.test(mobile)){
    ons.notification.alert('手机格式有误');
    return;

    if(newpassword.length <6){
        ons.notification.alert('密码至少需要6个字符');
        return;
    }

    }
    $.ajax(
        {
            method :'post',
            url:'/url/identity_check',
            data: {mobile: mobile,code:code,newpassword:newpassword,confirmnewpassword:confirmnewpassword},
            dataType:'json'
        }).done(function (data) {
        if (data.result =='success'){
            ons.notification.alert(data.msg).then(function () {
                fn.load('login.html');
            })
        }
        else{
            ons.notification.alert(data.msg)
        }
    });

}

 // demo登录
window.fn.User.ajaxlogin = function () {
    var username = $('#ajax-user-login #username').val()
    var password = $('#ajax-user-login #password').val()

    $.ajax(
        {
            method:'post',
            url:'/user/ajax_login',
            data:{login_name: username,login_pass:password},
            dataType:'json'
    }).done(function(data){
        if(data.result == 'successful'){
            localStorage.setItem('wx-user-name',username); //存储用户名
            localStorage.setItem('wx-user-id',data.msg); // user.id是判断用户是否登录的重要标准   存储msg,data.msg=user.id
            fn.load('profile.html');
            // ons.notification.alert('欢迎进入我的网站')

        }else{
            ons.notification.alert("测试用户不存在").then(function(){
                fn.User.clear()
            })
        }
    });

}

window.fn.User.clear = function(){   //localstorage里 清出记录
    localStorage.removeItem('wx-user-name');
    localStorage.removeItem('wx-user-id');
    localStorage.removeItem('wx-user-profile')
}

window.fn.User.getLoginId = function(){
    return localStorage.getItem('wx-user-id')
}

window.fn.User.getCreateForm = function(target){
    $.ajax({
            method: 'get',
            url:'/user/create',
            dataType:'html'
        }).done(function(data){
            $(target).html(data);
        });
}

//实现用户注册的ajax的接口

window.fn.User.getNumRegistered = function (target) {
    $.ajax({
        method:'get',
        url:'url/numregistered',
        dataType:'html',
    }).done(function (data) {
        $(target).html(data)
    })

}




window.fn.User.getConsoleHtml = function(target){
    $.ajax({
            method: 'post',
            url:'/user/console',
            data: {username: localStorage.getItem('wx-user-name'), user_id: localStorage.getItem('wx-user-id')},
            dataType:'html'
        }).done(function(data){
            $(target).html(data);
        });
}

window.fn.User.ajaxGetProfileHtml = function(target){
    $.ajax({
            method: 'post',
            url:'/user/profile',
            data: {username: localStorage.getItem('wx-user-name'), user_id: localStorage.getItem('wx-user-id')},
            dataType:'html'
        }).done(function(data){
            $(target).html(data);
        });
}

window.fn.User.ajaxUpdateProfile = function(f, v){
    var msg = '姓名';
    if(f == 'mobile')
        msg = '手机号码';
    if(f == 'id_no')
        msg = '身份证编号';

    ons.notification.prompt(msg,{defaultValue:v}).then(function(value){
        if(value == v)
            return;

        $.ajax({
            method:'post',
            url:'/user/update',
            data:{user_id: localStorage.getItem('wx-user-id'),flag:f,value:value},
            dataType:'json'
        }).done(function(data){
            if(data.result == 'success'){
                $('#user-update #'+f).html(value);
            }else{
                ons.notification.alert(data.msg);
            }
        });
    });
}

window.fn.User.ajaxWalletHtml = function(target){
    $.ajax({
            method: 'post',
            url:'/user/wallet',
            data: {username: localStorage.getItem('wx-user-name'), user_id: localStorage.getItem('wx-user-id')},
            dataType:'html'
        }).done(function(data){
            $(target).html(data);
        });
}

window.fn.User.ajaxOrdersHtml = function(target){
    $.ajax({
            method: 'post',
            url:'/user/orders',
            data: {username: localStorage.getItem('wx-user-name'), user_id: localStorage.getItem('wx-user-id')},
            dataType:'html'
        }).done(function(data){
            $(target).html(data);
        });
}

window.fn.User.ajaxWithdrawHtml = function(target){
    $.ajax({
            method: 'get',
            url:'/user/withdraw',
            data: {username: localStorage.getItem('wx-user-name'), user_id: localStorage.getItem('wx-user-id')},
            dataType:'html'
        }).done(function(data){
            $(target).html(data);
        });
}

window.fn.User.saveBankInfo = function(){
    var bank_no = $('#user-new-bank #bank_no').val();
    var bank_account_name = $('#user-new-bank #bank_account_name').val();
    var bank_province = $('#user-new-bank #bank_province').val();
    var bank_city = $('#user-new-bank #bank_city').val();
    var bank_name = $('#user-new-bank #bank_name').val();
    var bank_branch_name = $('#user-new-bank #bank_branch_name').val();
    var is_default = document.getElementById('check-is-default-bank').checked ? 1 : 0;

    var reg = /^\d+$/g

    if(!reg.test(bank_no)){
       ons.notification.alert('银行帐号格式有误!');
       return;
    }

    if(bank_account_name.length < 2){
       ons.notification.alert('帐号名称格式有误!');
       return;
    }

    if(bank_province.length<2){
       ons.notification.alert('所在省份格式有误!');
       return;
    }

    if(bank_city.length<2){
       ons.notification.alert('所在城市格式有误!');
       return;
    }

    if(bank_name.length<2){
       ons.notification.alert('开户银行格式有误!');
       return;
    }

    if(bank_branch_name.length<4){
       ons.notification.alert('所在支行格式有误!');
       return;
    }

    $.ajax({
            method: 'post',
            url:'/bank/create',
            data: {bank_no: bank_no, bank_account_name:bank_account_name,bank_province:bank_province,bank_city:bank_city,bank_name:bank_name,bank_branch_name:bank_branch_name,is_default:is_default, user_id: localStorage.getItem('wx-user-id')},
            dataType:'json'
        }).done(function(data){
            if(data.result=='success'){
                fn.load('user-update.html');
            }else{
                ons.notification.alert(data.msg);
            }
        });

}

window.fn.User.doWithdraw = function(maxValue){
    var bank_id = $('#user-withdraw #choose-bank-id').val();
    var amount = parseFloat($('#user-withdraw #withdraw-amount').val());

    if(isNaN(amount)){
        ons.notification.alert('提现金额格式有误!');
        return;
    }

    if(amount > parseFloat(maxValue)){
        ons.notification.alert('提现金额不得大于:'+maxValue+'!');
        return;
    }

    $.ajax({
        method:'post',
        url:'/user/withdraw',
        data:{user_id: localStorage.getItem('wx-user-id'),bank_id:bank_id,amount:amount},
        dataType:'json'
    }).done(function(data){
        if(data.result == 'success'){
            ons.notification.alert('您的提现申请已提交，我们会在T+1个工作日内处理完成，请耐心等待！').then(function(){
                fn.load('user-withdraw-history.html');
            });
        }else{
            ons.notification.alert(data.msg);
        }
    });

}

window.fn.User.ajaxWithdrawHistoryHtml = function(target){
    $.ajax({
            method: 'post',
            url:'/user/withdraw-history',
            data: {username: localStorage.getItem('wx-user-name'), user_id: localStorage.getItem('wx-user-id')},
            dataType:'html'
        }).done(function(data){
            $(target).html(data);
        });
}

window.fn.User.ajaxDepositHistoryHtml = function(target){
    $.ajax({
            method: 'post',
            url:'/user/deposit-history',
            data: {username: localStorage.getItem('wx-user-name'), user_id: localStorage.getItem('wx-user-id')},
            dataType:'html'
        }).done(function(data){
            $(target).html(data);
        });
}