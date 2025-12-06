import type {ReactNode} from 'react';
import clsx from 'clsx';
import Link from '@docusaurus/Link';
import useDocusaurusContext from '@docusaurus/useDocusaurusContext';
import Layout from '@theme/Layout';
import HomepageFeatures from '@site/src/components/HomepageFeatures';
import Heading from '@theme/Heading';

import styles from './index.module.css';

function HomepageHeader() {
  const {siteConfig} = useDocusaurusContext();
  return (
    <header className={clsx('hero hero--primary', styles.heroBanner)}>
      <div className="container">
        {/* Hero Title */}
        <Heading as="h1" className="hero__title" style={{color: '#e4eaf8'}}>
          {siteConfig.title}
        </Heading>

        {/* Hero Subtitle */}
        <p className="hero__subtitle" style={{color: '#a8b2c3', fontSize: '1.25rem', marginTop: '0.5rem'}}>
          {siteConfig.tagline}
        </p>

        {/* Buttons */}
        <div className={styles.buttons}>
          <Link
            className="button"
            to="/docs/intro"
            style={{
              backgroundColor: '#1b2a49',
              color: '#e4eaf8',
              boxShadow: '0 0 12px rgba(76,106,161,0.5)',
            }}
            onMouseOver={(e) => {
              (e.currentTarget as HTMLElement).style.backgroundColor = '#27406c';
              (e.currentTarget as HTMLElement).style.boxShadow = '0 0 18px rgba(76,106,161,0.7)';
            }}
            onMouseOut={(e) => {
              (e.currentTarget as HTMLElement).style.backgroundColor = '#1b2a49';
              (e.currentTarget as HTMLElement).style.boxShadow = '0 0 12px rgba(76,106,161,0.5)';
            }}
          >
            MY BOOK INTRO
          </Link>
        </div>
      </div>
    </header>
  );
}

export default function Home(): ReactNode {
  const {siteConfig} = useDocusaurusContext();
  return (
    <Layout
      title={`Welcome to ${siteConfig.title}`}
      description="A modern, Navy Blue themed Docusaurus site">
      <HomepageHeader />
      <main>
        <HomepageFeatures />
      </main>
    </Layout>
  );
}
