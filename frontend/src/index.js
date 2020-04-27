const PORTS = [5001, 5002, 5003, 5004];
const LOGS = {
  5001: [],
  5002: [],
  5003: [],
  5004: [],
};
const STATES = {
  5001: {},
  5002: {},
  5003: {},
  5004: {},
};
const IS_ASLEEP = {
  5001: false,
  5002: false,
  5003: false,
  5004: false,
};
const NUM_LOGS_TO_SHOW = 20;
const ROOT_URL = window.location.href.toString();

new ClipboardJS('.btn-clipboard');

const numNode = (node) => node % 5000;

PORTS.forEach(port => {
  $(`#sleep${numNode(port)}`).click(() => {
    if (IS_ASLEEP[port]) {
      $.post(`${ROOT_URL}${port}/wake_up`);
      $(`#sleep${numNode(port)}`).text("Sleep")
    } else {
      $.post(`${ROOT_URL}${port}/sleep`);
      $(`#sleep${numNode(port)}`).text("Wake up")
    }
    IS_ASLEEP[port] = !IS_ASLEEP[port];
  });

  $(`#reset${numNode(port)}`).click(() => {
    $.post(`${ROOT_URL}${port}/reset`);
    $(`#logs-node${numNode(port)}`).html("");
  });
});

function nameify(port) {
  return `${port} (${STATES[port].name})`
}

function timeify(timestamp) {
  return `${Math.round(Date.now() / 1000 - timestamp)} seconds ago`
}

function formatPeers(obj) {
  if (Object.keys(obj).length === 0) return "<i>None... node is peerless.</i>"
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

  let expectedFields = new Set([
    "peers",
    "name",
    "port",
    "biggest_prime",
    "biggest_prime_sender",
    "msg_id",
    "awake",
  ]);

  let html = [];
  html.push("<strong>Peers:</strong> " + formatPeers(json["peers"]));
  html.push("<strong>Biggest Mersenne prime:</strong> " + json["biggest_prime"]);
  html.push("<strong>Biggest Mersenne prime sender:</strong> " + nameify(json["biggest_prime_sender"]));
  html.push("<strong>Awake:</strong> " + json["awake"]);

  for (let field in json) {
    if (!expectedFields.has(field)) {
      html.push(`<strong>${field}</strong>: ${JSON.stringify(json[field])}`);
    }
  }

  html = html.map(el => "<li>" + el + "</li>" );

  $("ul#state-node" + numNode(port)).html(html.join(""));
  $("h3#name-node" + numNode(port)).text(nameify(port));
}

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
      $("div#errors" + numNode(port)).html(`<div class="alert alert-danger alert-dismissable">${errors.reverse().join("")}</div>`);
    } else {
      logs.push([
        "<li class=\"line\">",
        prefix,
        pairs.join(","),
        "</li>"
      ].join(""));
    }
  });
  $("ul#logs-node" + numNode(port)).html(logs.reverse().join(""));
}

setTimeout(() => {
  setInterval(() => {
    PORTS.forEach((port) => {
      $.getJSON(`${ROOT_URL}${port}/state`)
        .done((json) => setState(json, port))
        .fail((jqxhr, textStatus, err) => {
          $("ul#state-node" + numNode(port)).text("Node is not responding!")
        });
    });
  }, 1000);


  setInterval(() => {
    PORTS.forEach((port) => {
      $.getJSON(`${ROOT_URL}${port}/message_log`)
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

}, 4000); // Give the backend some time to get set up
