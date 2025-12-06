import type { ReactNode } from 'react';
import clsx from 'clsx';
import Heading from '@theme/Heading';
import styles from './styles.module.css';

type FeatureItem = {
  title: string;
  icon: string;
  description: ReactNode;
};

const FeatureList: FeatureItem[] = [
  {
    title: 'Physical AI Foundations',
    icon: '🤖',
    description: (
      <>
        Core robotics fundamentals including ROS2, URDF, controllers,  
        robot anatomy and the modern humanoid stack.
      </>
    ),
  },
  {
    title: 'NVIDIA Isaac & Digital Twin',
    icon: '🧠',
    description: (
      <>
        Learn high-fidelity simulation, sensor pipelines, VSLAM,  
        reinforcement learning and digital-twin workflows.
      </>
    ),
  },
  {
    title: 'Voice → Action VLA Pipeline',
    icon: '🎤',
    description: (
      <>
        Whisper + LLM-based command interpretation, cognitive planning,  
        grounding, navigation and manipulation execution.
      </>
    ),
  },
];

function Feature({ title, icon, description }: FeatureItem) {
  return (
    <div className={clsx('col col--4')}>
      <div className={styles.card}>
        <div className={styles.icon}>{icon}</div>
        <Heading as="h3" className={styles.title}>
          {title}
        </Heading>
        <p className={styles.text}>{description}</p>
      </div>
    </div>
  );
}

export default function HomepageFeatures(): ReactNode {
  return (
    <section className={styles.featuresSection}>
      <div className="container">
        <div className="row">
          {FeatureList.map((props, idx) => (
            <Feature key={idx} {...props} />
          ))}
        </div>
      </div>
    </section>
  );
}
