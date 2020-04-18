const PORTS = [5000, 5001, 5002, 5003];
const LOGS = {
  5000: [],
  5001: [],
  5002: [],
  5003: [],
};
const STATES = {
  5000: {},
  5001: {},
  5002: {},
  5003: {},
};
const IS_ASLEEP = {
  5000: false,
  5001: false,
  5002: false,
  5003: false,
};
const NUM_LOGS_TO_SHOW = 20;

new ClipboardJS('.btn-clipboard');

[0, 1, 2, 3].forEach(node => {
  $(`#sleep${node}`).click(() => {
    let port = 5000 + node;

    if (IS_ASLEEP[port]) {
      $.post(`http://localhost:${port}/wake_up`);
      $(`#sleep${node}`).text("Sleep")
    } else {
      $.post(`http://localhost:${port}/sleep`);
      $(`#sleep${node}`).text("Wake up")
    }
    IS_ASLEEP[port] = !IS_ASLEEP[port];
  });
});

function nameify(port) {
  return `${port} (${STATES[port].name})`
}

function timeify(timestamp) {
  return `${Math.round(Date.now() / 1000 - timestamp)} seconds ago`
}

function formatPeers(obj) {
  let s = "";
  for (let peer in obj) {
    s += `${nameify(peer)}: ${timeify(obj[peer])}</br>`
  }
  return s;
}

function setState(json, port) {
  // If no changes in state, don't change the DOM.
  if (STATES[port] === json) return;
  // Set new state
  STATES[port] = json;

  let html = [];
  html.push("<strong>Peers:</strong> " + formatPeers(json["peers"]));
  html.push("<strong>Biggest Mersenne prime:</strong> " + json["biggest_prime"]);
  html.push("<strong>Biggest Mersenne prime sender:</strong> " + nameify(json["biggest_prime_sender"]));
  html = html.map(el => "<li>" + el + "</li>" );

  let num = port % 5000;
  $("ul#state-node" + num).html(html.join(""));
  $("h3#name-node" + num).text(nameify(port));
}

setInterval(() => {
  PORTS.forEach((port) => {
    $.getJSON("http://localhost:" + port)
      .done((json) => setState(json, port))
      .fail((jqxhr, textStatus, err) => {
        $("ul#state-node" + (port - 5000)).text("Node is not responding!")
      });
  });
}, 1000);


setInterval(() => {
  PORTS.forEach((port) => {
    $.getJSON("http://localhost:" + port + "/message_log")
      .done((json) => {
        // dedup logs
        let shouldUpdate = false;
        json.forEach(log => {
          let s = JSON.stringify(log);
          if (!LOGS[port].includes(s)) {
            LOGS[port].push(s);
            shouldUpdate = true;
          }
        });

        if (shouldUpdate) updateLogs(port);
      })
      .fail((jqxhr, textStatus, err) => {
        console.log([jqxhr, textStatus, err]);
      });
  });
}, 200);

function updateLogs(port) {
  let logs = [];
  let errors = [];
  LOGS[port].slice(-NUM_LOGS_TO_SHOW).forEach(log => {
    let json = JSON.parse(log);
    let received = !!(json["received"]);
    let prefix = received ? "RECEIVED:" : "SENT:";
    let isError = "error" in json;
    delete json["received"];

    let pairs = [];
    for (let key in json) pairs.push(key + "=" + json[key]);

    if (isError) {
      errors.push([
        "<li class=\"line\">",
        pairs.join(","),
        "</li>"
      ].join(""));
      $("div#errors" + port % 5000).html(`<div class="alert alert-danger alert-dismissable">${errors.reverse().join("")}</div>`);
    } else {
      logs.push([
        "<li class=\"line\">",
        prefix,
        pairs.join(","),
        "</li>"
      ].join(""));
    }
  });
  $("ul#logs-node" + port % 5000).html(logs.reverse().join(""));
}
