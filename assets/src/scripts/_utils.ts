// From https://docs.djangoproject.com/en/3.0/ref/csrf/
export function getCookie(name: string) {
  let cookieValue: string | undefined;
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

export async function postFetchWithOptions({
  body,
  url,
}: {
  body: Record<string, unknown>;
  url: string;
}) {
  const requestHeaders = new Headers();
  requestHeaders.append("Accept", "application/json");
  requestHeaders.append("Content-Type", "application/json");

  const csrfCookie = getCookie("csrftoken");
  if (csrfCookie) {
    requestHeaders.append("X-CSRFToken", csrfCookie);
  }

  const response = await fetch(url, {
    method: "POST",
    credentials: "include" as RequestCredentials,
    mode: "same-origin" as RequestMode,
    headers: requestHeaders,
    body: JSON.stringify(body),
  });

  if (!response.ok) {
    throw new Error("Something went wrong.");
  }
  return await response.json();
}
