// const PORTS = [5000, 5001, 5002, 5003];
const PORTS = [5001, 5002]; // FIX THIS
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
const NUM_LOGS_TO_SHOW = 10;

const graph = new Springy.Graph();

jQuery(() => {
  var springy = jQuery('#springy').springy({
    graph: graph
  });
});

function setState(json, port) {
  if (Object.keys(STATES[port]).length === 0) {
    STATES[port] = json;
    updateGraph(port);
  }
  // If no changes in state, don't change the DOM.
  if (STATES[port] === json) return;
  STATES[port] = json;

  let html = [];
  html.push("<strong>Peers:</strong> " + JSON.stringify(json["peers"]));
  html.push("<strong>Port:</strong> " + JSON.stringify(json["port"]));
  html.push("<strong>Biggest prime:</strong> " + JSON.stringify(json["biggest_prime"]));
  html.push("<strong>Biggest prime sender:</strong> " + JSON.stringify(json["biggest_prime_sender"]));
  html = html.map(el => "<li>" + el + "</li>" );

  let num = port % 5000;
  $("ul#state-node" + num).html(html.join(""));
  $("h3#name-node" + num).text(json["name"]);
}

setInterval(() => {
  PORTS.forEach((port) => {
    $.getJSON("http://localhost:" + port)
      .done((json) => setState(json, port))
      .fail((jqxhr, textStatus, err) => {
        console.log([jqxhr, textStatus, err]);
        $("ul#state-node" + num).html("Node is not responding")
      });
  });
}, 1000);


setInterval(() => {
  PORTS.forEach((port) => {
    $.getJSON("http://localhost:" + port + "/message_log")
      .done((json) => {
        // dedup logs and make sure there are only 5; use hash as key?
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
  LOGS[port].slice(-NUM_LOGS_TO_SHOW).forEach(log => {
    let json = JSON.parse(log);
    let sent = !!(json["sent"]);
    let prefix = sent ? "SENT:" : "RECEIVED:";
    delete json["sent"];

    let pairs = [];
    for (let key in json) pairs.push(key + "=" + json[key]);
    logs.push([
      "<li class=\"line\">",
      prefix,
      pairs.join(","),
      "</li>"
    ].join(""));
  });
  $("ul#logs-node" + port % 5000).html(logs.join(""));
}

function updateGraph(port) {
  graph.addNodes(STATES[port].name);
  Object.keys(STATES[port].peers).forEach(peer => {
    graph.addEdges([STATES[port].name, STATES[peer].name], { color: '#000000' });
  });
}
