const canvas = document.getElementById('confettiCanvas');
const ctx = canvas.getContext('2d');
let particles = [];

function resizeCanvas() {
  canvas.width = window.innerWidth;
  canvas.height = window.innerHeight;
}

function createParticles() {
  const colors = ['#ffd6e7', '#fff0a8', '#c5f6fa', '#f8d7ff', '#ffffff'];
  particles = Array.from({ length: 120 }, () => ({
    x: Math.random() * canvas.width,
    y: Math.random() * canvas.height - canvas.height,
    w: Math.random() * 8 + 4,
    h: Math.random() * 14 + 6,
    speed: Math.random() * 2 + 1,
    drift: Math.random() * 1.2 - 0.6,
    color: colors[Math.floor(Math.random() * colors.length)],
    rotation: Math.random() * Math.PI,
  }));
}

function draw() {
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  particles.forEach((p) => {
    ctx.save();
    ctx.translate(p.x, p.y);
    ctx.rotate(p.rotation);
    ctx.fillStyle = p.color;
    ctx.fillRect(-p.w / 2, -p.h / 2, p.w, p.h);
    ctx.restore();

    p.y += p.speed;
    p.x += p.drift;
    p.rotation += 0.02;
    if (p.y > canvas.height + 20) {
      p.y = -20;
      p.x = Math.random() * canvas.width;
    }
  });
  requestAnimationFrame(draw);
}

resizeCanvas();
createParticles();
draw();
window.addEventListener('resize', () => {
  resizeCanvas();
  createParticles();
});
