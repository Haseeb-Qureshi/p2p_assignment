jQuery(() => {
  let width = 1000;
  let height = 400;
  var layout = new Springy.Layout.ForceDirected(
    graph,
    300.0, // Spring stiffness
    400.0, // Node repulsion
    0.5 // Damping
  );

  var canvas = document.getElementById('springy');
  var ctx = canvas.getContext('2d');

  var renderer = new Springy.Renderer(layout,
    function clear() {
      ctx.clearRect(0, 0, width, height);
    },
    function drawEdge(edge, p1, p2) {
      ctx.save();
      ctx.translate(width/2, height/2);

      ctx.strokeStyle = 'rgba(0,0,0,0.15)';
      ctx.lineWidth = 2.0;

      ctx.beginPath();
      ctx.moveTo(p1.x * 50, p1.y * 40);
      ctx.lineTo(p2.x * 50, p2.y * 40);
      ctx.stroke();

      ctx.restore();
    },
    function drawNode(node, p) {
      ctx.save();
      ctx.translate(width/2, height/2);

      ctx.font = "12px 'IM Fell English', 'Times New Roman', serif";

      var width = ctx.measureText(node.data.label).width;
      var x = p.x * 50;
      var y = p.y * 40;
      ctx.clearRect(x - width / 2.0 - 2, y - 10, width + 4, 20);
      ctx.fillStyle = '#000000';
      ctx.fillText(node.data.label, x - width / 2.0, y + 5);

      ctx.restore();
    }
  );

  renderer.start();
});
