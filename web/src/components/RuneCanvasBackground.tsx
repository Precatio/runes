"use client";
import React, { useEffect, useRef } from 'react';

const RuneCanvasBackground: React.FC = () => {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let animationFrameId: number;
    let width = (canvas.width = window.innerWidth);
    let height = (canvas.height = window.innerHeight);

    interface RuneNode {
      x: number;
      y: number;
      vx: number;
      vy: number;
      radius: number;
      char: string;
    }

    const runicAlphabet = ["ᚢᛚᚠᛦ", "ᛒᛁᚢᚱᚾ", "ᛋᛏᛁᚾ", "ᚱᛁᛋᛏᛁ", "ᚴᚢᚦ", "ᚠᛅᚦᚢᚱ", "ᛋᚢᚾ", "ᛅᚢᚴ", "ᛒᚱᚢᚦᚢᚱ", "ᚼᛁᛅᛚᛒᛁ", "ᛅᚾᛏ"];
    const nodes: RuneNode[] = [];
    // Calculate number of nodes based on screen size, keep it sparse and subtle
    const numNodes = Math.min(60, Math.floor((width * height) / 20000));

    const mouse = { x: -1000, y: -1000, active: false };

    const handleMouseMove = (e: MouseEvent) => {
      mouse.x = e.clientX;
      mouse.y = e.clientY;
      mouse.active = true;
    };

    const handleMouseLeave = () => {
      mouse.active = false;
    };

    window.addEventListener('mousemove', handleMouseMove);
    document.addEventListener('mouseleave', handleMouseLeave);

    for (let i = 0; i < numNodes; i++) {
      nodes.push({
        x: Math.random() * width,
        y: Math.random() * height,
        vx: (Math.random() - 0.5) * 0.2, // Very slow movement
        vy: (Math.random() - 0.5) * 0.2,
        radius: Math.random() * 1.5 + 1,
        char: runicAlphabet[Math.floor(Math.random() * runicAlphabet.length)]
      });
    }

    const draw = () => {
      try {
        ctx.clearRect(0, 0, width, height);

        // Draw node-to-node connection lines
        ctx.lineWidth = 0.5;
        for (let i = 0; i < nodes.length; i++) {
          for (let j = i + 1; j < nodes.length; j++) {
            const dx = nodes[i].x - nodes[j].x;
            const dy = nodes[i].y - nodes[j].y;
            const dist = Math.sqrt(dx * dx + dy * dy);

            // Connect nodes that are close to each other
            if (dist < 350) {
              const alpha = (1 - dist / 350) * 0.25; // More visible lines
              ctx.strokeStyle = `rgba(148, 163, 184, ${alpha})`; // slate-400
              ctx.beginPath();
              ctx.moveTo(nodes[i].x, nodes[i].y);
              ctx.lineTo(nodes[j].x, nodes[j].y);
              ctx.stroke();
            }
          }
        }

        // Draw connections from nodes to mouse cursor
        if (mouse.active) {
          nodes.forEach(node => {
            const dx = mouse.x - node.x;
            const dy = mouse.y - node.y;
            const dist = Math.sqrt(dx * dx + dy * dy);
            if (dist < 200) {
              const alpha = (1 - dist / 200) * 0.2;
              ctx.strokeStyle = `rgba(148, 163, 184, ${alpha})`;
              ctx.lineWidth = 0.5;
              ctx.beginPath();
              ctx.moveTo(node.x, node.y);
              ctx.lineTo(mouse.x, mouse.y);
              ctx.stroke();
            }
          });
        }

        // Update and draw nodes
        nodes.forEach(node => {
          // Physics: slight pull towards mouse
          if (mouse.active) {
            const dx = mouse.x - node.x;
            const dy = mouse.y - node.y;
            const dist = Math.sqrt(dx * dx + dy * dy);
            const attractionRadius = 250;

            if (dist < attractionRadius && dist > 0.1) {
              const force = (1 - dist / attractionRadius) * 0.02;
              node.vx += (dx / dist) * force;
              node.vy += (dy / dist) * force;
            }
          }

          // Cap speed for fluid motion
          const maxSpeed = 0.8;
          const speed = Math.sqrt(node.vx * node.vx + node.vy * node.vy);
          if (speed > maxSpeed) {
            node.vx = (node.vx / speed) * maxSpeed;
            node.vy = (node.vy / speed) * maxSpeed;
          }

          // Friction
          node.vx *= 0.99;
          node.vy *= 0.99;

          // Keep minimum ambient drift
          if (Math.abs(node.vx) < 0.02) node.vx += (Math.random() - 0.5) * 0.02;
          if (Math.abs(node.vy) < 0.02) node.vy += (Math.random() - 0.5) * 0.02;

          node.x += node.vx;
          node.y += node.vy;

          // Screen wrapping
          if (node.x < -20) node.x = width + 20;
          if (node.x > width + 20) node.x = -20;
          if (node.y < -20) node.y = height + 20;
          if (node.y > height + 20) node.y = -20;

          // Draw the rune character instead of a circle
          ctx.font = '20px serif'; // slightly smaller than before
          ctx.fillStyle = 'rgba(148, 163, 184, 0.4)'; // slate-400 with lower opacity
          ctx.textAlign = 'center';
          ctx.textBaseline = 'middle';
          ctx.fillText(node.char, node.x, node.y);
        });
      } catch (e) {
        console.error('Canvas draw animation error:', e);
      }

      animationFrameId = requestAnimationFrame(draw);
    };

    draw();

    const handleResize = () => {
      if (!canvas) return;
      width = canvas.width = window.innerWidth;
      height = canvas.height = window.innerHeight;
    };
    window.addEventListener('resize', handleResize);

    return () => {
      cancelAnimationFrame(animationFrameId);
      window.removeEventListener('resize', handleResize);
      window.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseleave', handleMouseLeave);
    };
  }, []);

  return (
    <canvas
      ref={canvasRef}
      className="absolute inset-0 w-full h-full pointer-events-none z-0"
      style={{ opacity: 0.8 }} // Subtle opacity
    />
  );
};

export default RuneCanvasBackground;
