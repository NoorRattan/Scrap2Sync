"use client";

import { Canvas, useFrame } from "@react-three/fiber";
import { useRef } from "react";
import type { Mesh } from "three";

function OrbMesh({ reducedMotion }: { reducedMotion: boolean }) {
  const mesh = useRef<Mesh>(null);

  useFrame((state, delta) => {
    if (!mesh.current || reducedMotion || document.hidden) return;
    mesh.current.rotation.x += delta * 0.08;
    mesh.current.rotation.y += delta * 0.13;
    const pulse = 1 + Math.sin(state.clock.elapsedTime * 0.8) * 0.035;
    mesh.current.scale.setScalar(pulse);
  });

  return (
    <mesh ref={mesh} rotation={[0.35, 0.25, 0]}>
      <icosahedronGeometry args={[1, 3]} />
      <meshPhysicalMaterial
        color="#22d3ee"
        emissive="#075985"
        emissiveIntensity={0.7}
        metalness={0.35}
        roughness={0.28}
        transparent
        opacity={0.86}
        wireframe
      />
    </mesh>
  );
}

export function SyncOrb({ reducedMotion }: { reducedMotion: boolean }) {
  return (
    <Canvas
      aria-hidden="true"
      camera={{ position: [0, 0, 3.2], fov: 42 }}
      dpr={[1, 1.5]}
      frameloop={reducedMotion ? "demand" : "always"}
      gl={{ alpha: true, antialias: true, powerPreference: "low-power" }}
    >
      <ambientLight intensity={1.4} />
      <pointLight position={[2, 2, 3]} intensity={14} color="#a5f3fc" />
      <OrbMesh reducedMotion={reducedMotion} />
    </Canvas>
  );
}
