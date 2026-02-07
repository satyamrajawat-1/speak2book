const btn = document.createElement("button");

btn.innerHTML = "🎤";

btn.style.position = "fixed";
btn.style.bottom = "20px";
btn.style.right = "20px";
btn.style.zIndex = "9999";
btn.style.fontSize = "25px";

document.body.appendChild(btn);

btn.onclick = () => {

  const cmd = prompt("Command:");

  fetch("http://localhost:8000/command", {
    method:"POST",
    headers:{"Content-Type":"application/json"},
    body:JSON.stringify({text:cmd})
  });

};
