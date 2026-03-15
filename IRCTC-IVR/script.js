const session_id = Math.random().toString(36).substring(7)

function addMessage(sender,text){

const chat=document.getElementById("chat")

const msg=document.createElement("div")

msg.className=sender=="User"?"user":"system"

msg.innerHTML="<b>"+sender+":</b> "+text

chat.appendChild(msg)

chat.scrollTop=chat.scrollHeight
}

async function sendText(){

const input=document.getElementById("textInput")

const text=input.value

if(text=="") return

addMessage("User",text)

const res=await fetch("http://127.0.0.1:8000/chat",{

method:"POST",

headers:{"Content-Type":"application/json"},

body:JSON.stringify({

session_id:session_id,

text:text

})

})

const data=await res.json()

addMessage("System",data.reply)

document.getElementById("debug").innerText=
JSON.stringify(data.debug,null,2)

speak(data.reply)

input.value=""
}

function quick(text){

document.getElementById("textInput").value=text

sendText()
}

function speak(text){

const speech=new SpeechSynthesisUtterance(text)

speech.lang="en-IN"

speech.rate=1

window.speechSynthesis.speak(speech)
}

function startSpeech(){

const SpeechRecognition=
window.SpeechRecognition||window.webkitSpeechRecognition

const recognition=new SpeechRecognition()

recognition.lang="en-IN"

recognition.start()

recognition.onresult=function(event){

const text=event.results[0][0].transcript

document.getElementById("textInput").value=text

sendText()

}
}

function resetConversation(){

location.reload()

}