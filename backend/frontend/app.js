async function sendMessage(){

const input =
document.getElementById(
"message"
);

const text =
input.value;

const response =
await fetch(
"http://127.0.0.1:8000/chat",
{
method:"POST",
headers:{
"Content-Type":
"application/json"
},
body:JSON.stringify({
user_id:"ennio",
message:text
})
}
);

const data =
await response.json();

document
.getElementById("chat")
.innerHTML +=
"<p><b>Tú:</b> "
+ text +
"</p>";

document
.getElementById("chat")
.innerHTML +=
"<p><b>Tercero:</b> "
+ data.text +
"</p>";

input.value="";
}