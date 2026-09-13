"use client";

import { Canvas, useFrame } from "@react-three/fiber";
import { ContactShadows, Environment, Lightformer } from "@react-three/drei";
import {
  Bloom,
  DepthOfField,
  EffectComposer,
} from "@react-three/postprocessing";
import { useMemo, useRef } from "react";
import { MathUtils, type Group, type Points } from "three";

function Sculpture({ reducedMotion }: { reducedMotion: boolean }) {
  const group = useRef<Group>(null);
  const dust = useRef<Points>(null);
  const elapsed = useRef(0);
  const particles = useMemo(() => {
    const positions = new Float32Array(54 * 3);
    for (let i = 0; i < 54; i++) {
      const angle = i * 2.399963;
      const radius = 1.6 + ((i * 17) % 23) / 12;
      positions.set(
        [
          Math.cos(angle) * radius,
          Math.sin(angle) * radius * 0.8,
          Math.sin(i * 7) * 1.9 - 1,
        ],
        i * 3,
      );
    }
    return positions;
  }, []);
  useFrame(({ camera, pointer }, delta) => {
    if (reducedMotion || document.hidden || !group.current) return;
    elapsed.current += Math.min(delta, 0.05);
    const time = elapsed.current;
    group.current.rotation.y = time * 0.095;
    group.current.rotation.z = Math.sin(time * 0.2) * 0.12;
    group.current.position.y = Math.sin(time * 0.65) * 0.085;
    camera.position.x = MathUtils.damp(
      camera.position.x,
      pointer.x * 0.5,
      2,
      delta,
    );
    camera.position.y = MathUtils.damp(
      camera.position.y,
      0.35 + pointer.y * 0.28,
      2,
      delta,
    );
    camera.lookAt(0, 0, 0);
    if (dust.current) dust.current.rotation.y = time * -0.018;
  });
  return (
    <>
      <group ref={group}>
        <mesh rotation={[0.55, 0.15, -0.35]} castShadow receiveShadow>
          <torusKnotGeometry args={[1.12, 0.34, 192, 32, 2, 3]} />
          <meshPhysicalMaterial
            color="#a9bfae"
            metalness={0.92}
            roughness={0.22}
            clearcoat={1}
            clearcoatRoughness={0.2}
            envMapIntensity={1.25}
          />
        </mesh>
        <mesh rotation={[1.1, -0.6, 0.25]}>
          <torusGeometry args={[1.93, 0.009, 6, 128, Math.PI * 1.7]} />
          <meshStandardMaterial
            color="#d8e9b0"
            emissive="#9db576"
            emissiveIntensity={1.1}
            metalness={0.7}
            roughness={0.32}
          />
        </mesh>
        <mesh position={[1.6, 0.78, 0.2]}>
          <sphereGeometry args={[0.045, 12, 12]} />
          <meshStandardMaterial
            color="#edfad6"
            emissive="#cceab0"
            emissiveIntensity={2.2}
          />
        </mesh>
      </group>
      <points ref={dust}>
        <bufferGeometry>
          <bufferAttribute attach="attributes-position" args={[particles, 3]} />
        </bufferGeometry>
        <pointsMaterial
          color="#c9dfbc"
          size={0.012}
          transparent
          opacity={0.65}
          sizeAttenuation
          depthWrite={false}
        />
      </points>
    </>
  );
}

export function SyncOrb({ reducedMotion }: { reducedMotion: boolean }) {
  const enhanced =
    typeof window !== "undefined" && window.innerWidth >= 900 && !reducedMotion;
  return (
    <Canvas
      aria-hidden="true"
      camera={{ position: [0, 0.35, 7.3], fov: 40 }}
      dpr={[1, 1.5]}
      frameloop={reducedMotion ? "demand" : "always"}
      gl={{ alpha: true, antialias: true, powerPreference: "low-power" }}
    >
      <ambientLight intensity={0.3} />
      <spotLight
        position={[-3, 5, 4]}
        intensity={35}
        angle={0.5}
        penumbra={1}
        color="#eff5dc"
      />
      <Environment resolution={128} frames={1}>
        <Lightformer
          form="rect"
          intensity={4}
          position={[-3, 3, 3]}
          scale={[3, 5, 1]}
          target={[0, 0, 0]}
          color="#f3f0db"
        />
        <Lightformer
          form="rect"
          intensity={2.5}
          position={[3, 1, 2]}
          scale={[1, 4, 1]}
          target={[0, 0, 0]}
          color="#c3deb8"
        />
        <Lightformer
          form="rect"
          intensity={5}
          position={[0, 4, -3]}
          scale={[4, 2, 1]}
          target={[0, 0, 0]}
          color="#faf9ed"
        />
        <Lightformer
          form="rect"
          intensity={1.5}
          position={[-2, -2, 1]}
          scale={[3, 1, 1]}
          target={[0, 0, 0]}
          color="#658474"
        />
      </Environment>
      <Sculpture reducedMotion={reducedMotion} />
      <ContactShadows
        position={[0, -1.95, 0]}
        opacity={0.32}
        scale={8}
        blur={2.8}
        far={4}
        resolution={128}
        frames={1}
        color="#050907"
      />
      {enhanced && (
        <EffectComposer multisampling={0}>
          <Bloom luminanceThreshold={1.5} intensity={0.22} mipmapBlur />
          <DepthOfField
            target={[0, 0, 0]}
            focalLength={0.08}
            bokehScale={0.7}
            height={240}
          />
        </EffectComposer>
      )}
    </Canvas>
  );
}
