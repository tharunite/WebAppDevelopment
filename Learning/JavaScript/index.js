let username;
document.getElementById("Submit").onclick=function(){
    username=document.getElementById('nametext').value;
    document.getElementById('mainH').textContent='Your Name';
    document.getElementById('mainP').textContent=`hello ${username}. Nice to meet you`;

    document.getElementById('nametext').style.display = 'none';
    document.getElementById('Submit').style.display = 'none';
}