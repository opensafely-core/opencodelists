// From https://docs.djangoproject.com/en/3.0/ref/csrf/
export function getCookie(name: string) {
  let cookieValue;
  if (document.cookie && document.cookie !== "") {
    const cookies = document.cookie.split(";");
    for (let i = 0; i < cookies.length; i++) {
      const cookie = cookies[i].trim();
      // Does this cookie string begin with the name we want?
      if (cookie.substring(0, name.length + 1) === `${name}=`) {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
}

export function readValueFromPage(id: string) {
  const scriptId = document.getElementById(id) as HTMLScriptElement;
  if (scriptId?.textContent) {
    return JSON.parse(scriptId.textContent);
  }
}
