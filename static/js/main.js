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

function getModal(button){
$.ajax({
  url: "/set",
  type: "GET",
  data: {
    csrf_token: csrf_token,
    type: "events",
    id: button.id,
    },
  success: function (response) {
    if (response.code == "200") {
    var modal = button.parentElement.parentElement.parentElement.querySelector(".eventmodalbase")
    date = new Date(response.date)
    modal.dataset.eventid = button.id
    modal.querySelector("#baseEventName").value = response.name;


modal.querySelector("#baseEventImgDisplay").src = 'static/img/' +response.imglink;

modal.querySelector("#baseEventDts").value = response.details;


modal.querySelector("#baseEventDate").value = date.toISOString().slice(0, 10);

modal.querySelector("#baseEventDtlink").value = response.dtlink;

modal.querySelector("#baseEventPrice").value =parseFloat(response.price);
    $("#existingEventModal").modal('show')
  } 
},
})
}
function HandleBaseFormChange(form){
    var modal = form.parentElement.parentElement.parentElement.parentElement 
    modal.dataset.isChanged = "true"
    console.log(modal.id)

}

function saveChanges(button){

    var form  = button.parentElement.parentElement.parentElement.parentElement.parentElement.parentElement
    console.log(modal.id) // I also dont know what to do here 6
//Get the modal overral parent, and check the changed flag
 if (modal.dataset.IsChanged){
    //pass an ajax request again
 }
}