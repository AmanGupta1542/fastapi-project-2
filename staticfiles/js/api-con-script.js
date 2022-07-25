// Script
var base_url = 'http://127.0.0.1:8000/api/';
var path_location = window.location.pathname;

if(localStorage.getItem('access_token') != null){
    window.location = "../client_dashboard/index.html";
}

function login(event){
    event.preventDefault();
    
    var email = document.getElementById("email").value;
    var password = document.getElementById("password").value;
    [wrong_cred, email_err, pass_err] = document.getElementsByClassName("error");

    if(email == "" && password == ""){
        email_err.textContent = "Email is required";
        pass_err.textContent = "Password is required";
        wrong_cred.textContent = "";
        return false;
    }
    else if(email == ''){
        email_err.textContent = "Email is required";
        wrong_cred.textContent = "";
        pass_err.textContent = "";
        return false;
    }
    else if(password == ''){
        pass_err.textContent = "Password is required";
        wrong_cred.textContent = "";
        email_err.textContent = "";
        return false;
    }
    else{
        req_data = {
            "email": email,
            "password": password
        }
        var response = fetch(base_url + 'users/login', {
            method: 'POST', // *GET, POST, PUT, DELETE, etc.
            mode: 'cors', // no-cors, *cors, same-origin
            cache: 'no-cache', // *default, no-cache, reload, force-cache, only-if-cached
            credentials: 'same-origin', // include, *same-origin, omit
            headers: {
            'Content-Type': 'application/json'
            // 'Content-Type': 'application/x-www-form-urlencoded',
            },
            redirect: 'follow', // manual, *follow, error
            referrerPolicy: 'no-referrer', // no-referrer, *no-referrer-when-downgrade, origin, origin-when-cross-origin, same-origin, strict-origin, strict-origin-when-cross-origin, unsafe-url
            body: JSON.stringify(req_data) // body data type must match "Content-Type" header
        });

        response.then(res => res.json())
        .then((res_data) => {
            // console.log(res_data);
            if(res_data.access_token != undefined || res_data.token_type != undefined){
                localStorage.setItem("access_token", res_data.access_token);
                localStorage.setItem("token_type", res_data.token_type);
                window.location = "../client_dashboard/index.html"; // Redirecting to other page.
            }
            else{
                if(res_data.detail != undefined){
                    wrong_cred.textContent = res_data.detail;
                    email_err.textContent = "";
                    pass_err.textContent = "";
                }
            }
        })
        .catch((error) => {
            alert('Something went wrong')
            console.error('Error:', error);
        });
    }
}

function reset_pass(event){
    event.preventDefault();
    var email = document.getElementById('email').value;
    if(email == ''){
        document.getElementsByClassName("success")[0].textContent = '';
        document.getElementsByClassName("error")[0].textContent = 'Email is required';
    }
    else{
        document.getElementsByClassName("error")[0].textContent = '';
        req_data = {
            "email": email
        }
        var response = fetch(base_url + 'users/forget-password', {
            method: 'POST', // *GET, POST, PUT, DELETE, etc.
            mode: 'cors', // no-cors, *cors, same-origin
            cache: 'no-cache', // *default, no-cache, reload, force-cache, only-if-cached
            credentials: 'same-origin', // include, *same-origin, omit
            headers: {
            'Content-Type': 'application/json'
            // 'Content-Type': 'application/x-www-form-urlencoded',
            },
            redirect: 'follow', // manual, *follow, error
            referrerPolicy: 'no-referrer', // no-referrer, *no-referrer-when-downgrade, origin, origin-when-cross-origin, same-origin, strict-origin, strict-origin-when-cross-origin, unsafe-url
            body: JSON.stringify(req_data) // body data type must match "Content-Type" header
        });

        response.then(res => res.json())
        .then((res_data) => {
            // console.log(res_data);
            if(res_data.message != undefined || res_data.status != undefined){
                document.getElementsByClassName("error")[0].textContent = '';
                document.getElementsByClassName("success")[0].textContent = res_data.message;
            }
            else{
                if(res_data.detail != undefined){
                    // console.log(res_data.detail[0].msg);
                    document.getElementsByClassName("success")[0].textContent = '';
                    document.getElementsByClassName("error")[0].textContent = res_data.detail;
                }
            }
        })
        .catch((error) => {
            alert('Something went wrong')
            console.error('Error:', error);
        });
    }
}

function reset_password(event){
    event.preventDefault();
    // console.log(window.location)
    var password = document.getElementById("password").value;
    var c_password = document.getElementById("confirm-password").value;
    [pass_err, c_pass_err] = document.getElementsByClassName("error");

    if(password == "" && c_password == ""){
        pass_err.textContent = "Password is required";
        c_pass_err.textContent = "Confirm password is required";
        return false;
    }
    else if(password == ''){
        pass_err.textContent = "Password is required";
        c_pass_err.textContent = "";
        return false;
    }
    else if(c_password == ''){
        c_pass_err.textContent = "Confirm Password is required";
        pass_err.textContent = "";
        return false;
    }
    else if(c_password != password){
        c_pass_err.textContent = "Passwords should be same";
        pass_err.textContent = "";
        return false;
    }
    else{
        req_data = {
            "password": password
        }
        let token = path_location.split("/").slice(-1)[0];
        var response = fetch(base_url + 'users/reset-password/' + token, {
            method: 'PATCH', // *GET, POST, PUT, DELETE, etc.
            mode: 'cors', // no-cors, *cors, same-origin
            cache: 'no-cache', // *default, no-cache, reload, force-cache, only-if-cached
            credentials: 'same-origin', // include, *same-origin, omit
            headers: {
            'Content-Type': 'application/json'
            // 'Content-Type': 'application/x-www-form-urlencoded',
            },
            redirect: 'follow', // manual, *follow, error
            referrerPolicy: 'no-referrer', // no-referrer, *no-referrer-when-downgrade, origin, origin-when-cross-origin, same-origin, strict-origin, strict-origin-when-cross-origin, unsafe-url
            body: JSON.stringify(req_data) // body data type must match "Content-Type" header
        });

        response.then(res => res.json())
        .then((res_data) => {
            // console.log(res_data);
            if (res_data.message != undefined && res_data.status != undefined){
                if(res_data.status == 'success'){
                    toastr.success('Password reset successfully', 'It says');
                    window.location = window.location.origin;
                }
                else{
                    pass_err.textContent = "";
                    c_pass_err.textContent = res_data.message;
                }
            }
        })
        .catch((error) => {
            pass_err.textContent = "";
            c_pass_err.textContent = 'Something went wrong';
            console.error('Error:', error);
        });
    }
}