"use strict";

// From https://docs.djangoproject.com/en/3.0/ref/csrf/
function getCookie(name) {
  let cookieValue = undefined;
  if (document.cookie && document.cookie !== "") {
    const cookies = document.cookie.split(";");
    for (let i = 0; i < cookies.length; i++) {
      const cookie = cookies[i].trim();
      // Does this cookie string begin with the name we want?
      if (cookie.substring(0, name.length + 1) === name + "=") {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
}

function readValueFromPage(id) {
  return JSON.parse(document.getElementById(id).textContent);
}

export { getCookie, readValueFromPage };
