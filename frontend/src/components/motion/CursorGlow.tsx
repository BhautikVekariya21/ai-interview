import { useEffect, useRef } from "react";

/**
 * A restrained, brand-coloured cursor halo for fine-pointer devices. It uses
 * direct compositor transforms rather than React state so cursor movement does
 * not cause application re-renders.
 */
export default function CursorGlow() {
  const glowRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const canUseEffect = window.matchMedia("(pointer: fine) and (prefers-reduced-motion: no-preference)");
    if (!canUseEffect.matches || !glowRef.current) return;

    const glow = glowRef.current;
    let frame = 0;
    let targetX = -200;
    let targetY = -200;
    let currentX = -200;
    let currentY = -200;
    let velocityX = 0;
    let velocityY = 0;
    let lastTime = 0;
    let hasPosition = false;

    const render = (time: number) => {
      const delta = Math.min((time - lastTime) / 1000, 0.032);
      lastTime = time;

      // A damped spring keeps the trail smooth even when the browser batches
      // pointer events or the pointer moves quickly between animation frames.
      velocityX += (targetX - currentX) * 300 * delta;
      velocityY += (targetY - currentY) * 300 * delta;
      velocityX *= Math.exp(-26 * delta);
      velocityY *= Math.exp(-26 * delta);
      currentX += velocityX * delta;
      currentY += velocityY * delta;
      glow.style.transform = `translate3d(${currentX}px, ${currentY}px, 0) translate(-50%, -50%)`;

      if (Math.abs(targetX - currentX) > 0.1 || Math.abs(targetY - currentY) > 0.1 || Math.abs(velocityX) > 0.1 || Math.abs(velocityY) > 0.1) {
        frame = window.requestAnimationFrame(render);
      } else {
        currentX = targetX;
        currentY = targetY;
        velocityX = 0;
        velocityY = 0;
        frame = 0;
      }
    };
    const move = (event: PointerEvent) => {
      targetX = event.clientX;
      targetY = event.clientY;
      if (!hasPosition) {
        currentX = targetX;
        currentY = targetY;
        hasPosition = true;
      }
      glow.style.opacity = "1";
      if (!frame) {
        lastTime = performance.now();
        frame = window.requestAnimationFrame(render);
      }
    };
    const show = () => { glow.style.opacity = "1"; };
    const hide = () => { glow.style.opacity = "0"; };

    window.addEventListener("pointermove", move, { passive: true });
    window.addEventListener("pointerenter", show);
    window.addEventListener("pointerleave", hide);

    return () => {
      window.cancelAnimationFrame(frame);
      window.removeEventListener("pointermove", move);
      window.removeEventListener("pointerenter", show);
      window.removeEventListener("pointerleave", hide);
    };
  }, []);

  return (
    <div
      ref={glowRef}
      aria-hidden="true"
      className="pointer-events-none fixed left-0 top-0 z-[100] flex h-14 w-14 items-center justify-center rounded-full border border-brand/60 bg-brand/15 opacity-0 shadow-[0_0_36px_hsl(var(--brand)/0.3)] transition-opacity duration-150"
    >
      <span className="h-1.5 w-1.5 rounded-full bg-brand" />
    </div>
  );
}
