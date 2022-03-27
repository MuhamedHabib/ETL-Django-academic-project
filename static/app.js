class Chatbox{
    constructor() {
        this.args={
            openButton: document.querySelector( '.chatbox__button'),
            chatBox: document.querySelector('.chatbox__support'),
            sendButton: document.querySelector('.send__button')

        }
        this.state=false;
        this.messages=[];

    }
    display(){
        const {openButton,chatBox,sendButton}=this.args;
        openButton.addEventListener('click',()=>this.toggleState(chatBox))
        sendButton.addEventListener('click',()=>this.onSendButton(chatBox))
        const node=chatBox.querySelector('input');
        node.addEventListener("keyup",({key})=>{
            if(key==="Enter"){
                this.onSendButton(chatBox)
            }
        })

    }
    toggleState(chatbox){
        this.state= !this.state;
        if(this.state){
            chatbox.classList.add('chatbox--active')
        }else {
            chatbox.classList.remove('chatbox--active')
        }
    }

    onSendButton(chatbox){
        var textField=chatbox.querySelector('input');
        let text1=textField.value
        if(text1==""){
            return;
        }
        let msg1={name:"User",message:text1}
        this.messages.push(msg1);


        fetch('http://localhost:8000/customer/predict',{
            method:'POST',
            body:JSON.stringify({message:text1}),
            mode:'cors',
            headers:{
                'Content-Type':'application/json',
                 'Accept': 'application/json',
                'X-Requested-With': 'XMLHttpRequest', //Necessary to work with request.is_ajax()
                'X-CSRFToken': csrftoken,

            },
        }).then(r=>r.json()).then(r=>{
            let msg2={name: "Sam",message:r.answer};
            this.messages.push(msg2);
            this.updateChatText(chatbox)
            textField.value=''
        }).catch((error)=>{
            console.error('Error:',error);
            this.updateChatText(chatbox)
            textField.value=''
        });

    }
    updateChatText(chatbox){
        var html='';
        this.messages.slice().reverse().forEach(function (item,){
            if(item.name==="Sam")
            {
                html+='<div class="messages__item messages__item--visitor">'+item.message+'</div>'

            }
            else
            {
                html+='<div class="messages__item messages__item--operator">'+item.message+'</div>'
            }
        });
        const chatmessage=chatbox.querySelector('.chatbox__messages');
        chatmessage.innerHTML=html;
    }

}
function getCookie(name) {
      let cookieValue = null;
      if (document.cookie && document.cookie !== '') {
          const cookies = document.cookie.split(';');
          for (let i = 0; i < cookies.length; i++) {
              const cookie = cookies[i].trim();
              // Does this cookie string begin with the name we want?
              if (cookie.substring(0, name.length + 1) === (name + '=')) {
                  cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                  break;
              }
          }
      }
      return cookieValue;
  }
  const csrftoken = getCookie('csrftoken');

const chatbox=new Chatbox();
chatbox.display();

