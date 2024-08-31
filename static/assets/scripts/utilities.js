// utilities.js
export function loader(element) {
  let loadInterval;
  element.textContent = "";

  loadInterval = setInterval(() => {
    element.textContent += ".";
    if (element.textContent === "....") {
      element.textContent = "";
    }
  }, 300);
  return loadInterval;
}

// export function typeText(element, text) {
//   return new Promise((resolve) => {
//     let index = 0;
//     const interval = setInterval(() => {
//       if (index < text.length) {
//         element.innerHTML += text.charAt(index);
//         index++;
//       } else {
//         clearInterval(interval);
//         resolve(); // Resolve the promise once the text is fully typed out
//       }
//     }, 5);
//   });
// }
export function typeText(element, text) {
  return new Promise((resolve) => {
    let index = 0;
    const interval = setInterval(() => {
      if (index < text.length) {
        element.innerHTML += text.charAt(index);
        index++;
      } else {
        clearInterval(interval);
        resolve();
      }
    }, 5);
  });
}

export function generateUniqueId() {
  const timestamp = Date.now();
  const randomNumber = Math.random().toString(36).substring(2, 15);
  return `id-${timestamp}-${randomNumber}`;
}

export function chatStripe(isAi, value, uniqueId, bot, user) {
  return `
    <div class="wrapper ${isAi ? "ai" : "user"}">
      <div class="chat">
        ${isAi ? `<div class="profile"><img src=${bot} alt="bot" /></div>` : ""}
        <div class="message ${isAi ? "left" : "right"}" id=${uniqueId}>${value}</div>
        ${
          !isAi
            ? `<div class="profile"><img src=${user} alt="user" /></div>`
            : ""
        }
      </div>
    </div>
  `;
}
