odoo.define("ai_internal_chatbot.stream", function (require) {
  const bus = require("bus.bus").bus;
  const session = require("web.session");

  let currentMessage = "";

  bus.on("notification", null, function (notifications) {
    for (let notif of notifications) {
      const channel = notif[0];
      const data = notif[1];

      if (channel.startsWith("ai_stream_")) {
        currentMessage += data.token;

        let container = document.querySelector(".o_MessageList");

        if (container) {
          let msg = document.getElementById("ai_stream_msg");

          if (!msg) {
            msg = document.createElement("div");
            msg.id = "ai_stream_msg";
            msg.className = "o_Message";
            container.appendChild(msg);
          }

          msg.innerText = currentMessage;
        }
      }
    }
  });

  bus.startPolling();
});
