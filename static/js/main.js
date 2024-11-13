const csrf_token = document.querySelector('meta[name="csrf_token"]').content;

document.addEventListener("DOMContentLoaded", function () {
  document.querySelectorAll(".deleteEventButton").forEach((button) => {
    button.addEventListener("click", () => {
      $.ajax({
        url: "/delete",
        type: "POST",
        data: {
          csrf_token: csrf_token,
          type: "event",
          id: button.id,
        },
        success: function (response) {
          location.reload();
        },
      })
    });
  });
  document.querySelectorAll(".deleteProdButton").forEach((button) => {
    button.addEventListener("click", () => {
      $.ajax({
        url: "/delete",
        type: "POST",
        data: {
          csrf_token: csrf_token,
          type: "product",
          id: button.id,
        },
        success: function (response) {
          location.reload();
        },
      })
    });
  });
  document.querySelectorAll(".AddProdButton").forEach((button) => {
    button.addEventListener("click", () => {
      image = document.querySelector("#newmodal").querySelector("#prodimg").files[0];
      reader = new FileReader();

      reader.onload = function() { 
        const imageb64 = reader.result.split(',')[1]            
        $.ajax({
        url: "/add",
        type: "POST",
        data: {
          csrf_token: csrf_token,
          type: "product",
          id: button.id,
          name:document.querySelector("#newmodal").querySelector("#prodname").value, 
          price: document.querySelector("#newmodal").querySelector("#prodprice").value,
          details: document.querySelector("#newmodal").querySelector("#proddts").value,
          imageb64: imageb64,
          },
        success: function (response) {
          console.log(response)
          setTimeout(() => {
      location.reload();
    }, 1000);
        },
      })
    }
    console.log(image)
    reader.readAsDataURL(image);

    });
  });

  document.querySelectorAll(".AddEventButton").forEach((button) => {
    button.addEventListener("click", () => {
      image = document.querySelector("#neweventmodal").querySelector("#eventimg").files[0];

      reader = new FileReader();

      reader.onload = function() { 
        const imageb64 = reader.result.split(',')[1]            
        $.ajax({
        url: "/add",
        type: "POST",
        data: {
          csrf_token: csrf_token,
          type: "event",
          id: button.id,
          name:document.querySelector("#neweventmodal").querySelector("#eventname").value, 
          date: document.querySelector("#neweventmodal").querySelector("#eventdate").value,
          details: document.querySelector("#neweventmodal").querySelector("#eventdts").value,
          dtlink: document.querySelector("#neweventmodal").querySelector("#dtlink").value,
          imageb64: imageb64,
          },
        success: function (response) {
          console.log(response)
          setTimeout(() => {
      location.reload();
    }, 1000);
        },
      })
    }
    reader.readAsDataURL(image);

    });
    
  });


});

function openNav() {
  document.getElementById("mySidenav").style.width = "180px";
}
function closeNav() {
  document.getElementById("mySidenav").style.width = "0";
}

function displayImage(input) {
  if (input.files && input.files[0]) {
    var reader = new FileReader();

    reader.onload = function (e) {
      $('#displayimg').attr('src', e.target.result).width(150).height(200);
    };

    reader.readAsDataURL(input.files[0]);
  }
}

function DropHandler(evt, parent) {
  evt.preventDefault();
  if (evt.dataTransfer.items) {
      [...evt.dataTransfer.items].forEach(item => {
          if (item.kind === 'file') {
              const file = item.getAsFile();
              if (file.type.startsWith('image/')) {
                  const reader = new FileReader();
                  reader.onload = function(e) {
                      const imgElement = parent.querySelector(".draginput");
                      console.log(imgElement)
                      if (imgElement) {
                          imgElement.src = e.target.result;
                          const dataTransfer = new DataTransfer();
                          dataTransfer.items.add(file);
                          imgElement.files = dataTransfer.files;
                          console.log(parent.querySelector(".draginput").files[0])
                          displayImage(parent.querySelector(".draginput"))
                      }
                  };
                  reader.onerror = function() {
                      console.error("Error reading file");
                  };
                  reader.readAsDataURL(file);
              }
          }
      });
  }
}

function dragOverHandler(ev) {
console.log("File(s) in drop zone");

// Prevent default behavior (Prevent file from being opened)
ev.preventDefault();
}

function getModal(button,newthing = false){
  const modal = button.parentElement.parentElement.parentElement.querySelector(".eventmodalbase")
  //add a switch to determine the type of modal to open

  switch (button.dataset.type){

    case "events":
      if (!newthing){ //Data alredy exists in DB, need to fetch 
        $.ajax({
          url: "/set",
          type: "GET",
          data: {
            csrf_token: csrf_token,
            type: button.dataset.type, //Button is not the modal one. Remeber that
            id: button.id,
            },
          success: function (response) {
            if (response.code == "200") {
            date = new Date(response.date)
            modal.dataset.eventid = button.id
            modal.dataset.type = response.type
            modal.querySelector("#EventName").value = response.name;
        
        modal.querySelector("#EventImgDisplay").src = 'static/img/' +response.imglink;
        
        modal.querySelector("#EventDts").value = response.details;
        
        
        modal.querySelector("#EventDate").value = date.toISOString().slice(0, 10);
        
        modal.querySelector("#EventDtlink").value = response.dtlink;
        
        modal.querySelector("#EventPrice").value =parseFloat(response.price);
            $("#EventModal").modal('show')
          } 
        },
        })
        }
        else { //Nothing in DB, need to clear modal 
        modal.dataset.eventid = "new"
        modal.dataset.type = button.dataset.type
          console.log("newthing")
        modal.querySelector("#EventName").value = "";
        modal.querySelector("#EventImgDisplay").src = undefined;
        modal.querySelector("#EventDts").value = "";
        modal.querySelector("#EventDate").value = "";
        if (modal.querySelector("#EventDtlink")) modal.querySelector("#EventDtlink").value = ""; //dtlink only exists on events
        modal.querySelector("#EventPrice").value = "";
        $("#EventModal").modal('show')
        
        }
        break;
  
    case "prods":
      if (!newthing){ //Data alredy exists in DB, need to fetch 
        $.ajax({
          url: "/set",
          type: "GET",
          data: {
            csrf_token: csrf_token,
            type: button.dataset.type, //Button is not the modal one. Remeber that
            id: button.id,
            },
          success: function (response) {
            if (response.code == "200") {
            date = new Date(response.date)
            modal.dataset.eventid = button.id
            modal.dataset.type = response.type
            modal.querySelector("#ProdName").value = response.name;
        
        modal.querySelector("#ProdImgDisplay").src = 'static/img/' +response.imglink;
        
        modal.querySelector("#ProdDts").value = response.details;
                
        modal.querySelector("#ProdPrice").value =parseFloat(response.price);
            $("#ProdModal").modal('show')
          } 
        },
        })
        }
        else { //Nothing in DB, need to clear modal 
        modal.dataset.eventid = "new"
        modal.dataset.type = button.dataset.type
          console.log("newthing")
        modal.querySelector("#ProdName").value = "";
        modal.querySelector("#ProdImgDisplay").src = undefined;
        modal.querySelector("#ProdDts").value = "";
        modal.querySelector("#ProdPrice").value = "";
        $("#ProdModal").modal('show')
        
        }

    break;
      }

}

async function GetFilefromURL(url) {

  const response = await fetch(url);
  const data = await response.blob();
  return new File([data], data.name, {
    type: data.type || data.type,
  });
}

async function saveChanges(button){
  var modal  = button.parentElement.parentElement.parentElement.parentElement.parentElement.parentElement

    // I also need a switch here yeeeeee
    switch (modal.dataset.type){

      case "events":

      image = modal.querySelector("#EventImg").files[0];
      console.log(image)
      if (image == undefined) {
        imageurl = modal.querySelector("#EventImgDisplay").src
      image = await GetFilefromURL(imageurl)
      }
  
      
      console.log(image)
  
      reader = new FileReader();
  
      reader.onload = function() { 
        console.log("starting ajax")
        const imageb64 = reader.result.split(',')[1]            
        $.ajax({
        url: "/update",
        type: "POST",
        data: {
          type: modal.dataset.type,
          csrf_token: csrf_token,
          id: modal.dataset.eventid,
          name:modal.querySelector("#EventName").value, 
          date: modal.querySelector("#EventDate").value,
          details: modal.querySelector("#EventDts").value,
          dtlink: modal.querySelector("#EventDtlink").value,
          imageb64: imageb64,
          price:modal.querySelector("#EventPrice").value,
          },
        success: function (response) {
          console.log(response)
          setTimeout(() => {
            location.reload();
    }, 1000);
        },
      })
    }
    reader.readAsDataURL(image);

        break;
      case "prods":
      image = modal.querySelector("#ProdImg").files[0];
      if (image == undefined) {
        imageurl = modal.querySelector("#ProdImgDisplay").src
      image = await GetFilefromURL(imageurl)
      }
  
  
      reader = new FileReader();
  
      reader.onload = function() { 
        const imageb64 = reader.result.split(',')[1]            
        $.ajax({
          url:"/update",
        type: "POST",
        data: {
          type: modal.querySelector('.eventmodalbase').dataset.type,
          csrf_token: csrf_token,
          id: modal.querySelector('.eventmodalbase').dataset.eventid,
          name:modal.querySelector("#ProdName").value, 
          details: modal.querySelector("#ProdDts").value,
          imageb64: imageb64,
          price:modal.querySelector("#ProdPrice").value,
          },
        success: function (response) {
          console.log(response)
          setTimeout(() => {
            location.reload();
    }, 1000);
        },
      })
    }
    reader.readAsDataURL(image);
        break;
    }

 
}

function editUser(user){
  modal = document.querySelector("#exampleModal")
  modal.querySelector("#editUserName").value = user
  modal.dataset.olduser = user
  $("#exampleModal").modal('show')
}

function saveUser(){
  modal = document.querySelector("#exampleModal")
  user = modal.dataset.olduser
  $.ajax({
    url: "/update",
    type: "POST",
    data: {
      csrf_token: csrf_token,
      type: "users",
      id: user,
      username: modal.querySelector("#editUserName").value,
      password: modal.querySelector("#editUserPassword").value,
    },
    success: function (response) {
      //location.reload();
    },
  })
}
function deleteUser(user){
  $.ajax({
    url: "/delete",
    type: "POST",
    data: {
      csrf_token: csrf_token,
      type: "user",
      id: user,
    },
    success: function (response) {
      location.reload();
    },
  })
}