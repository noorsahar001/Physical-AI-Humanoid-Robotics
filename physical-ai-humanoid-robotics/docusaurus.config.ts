import {themes as prismThemes} from 'prism-react-renderer';
import type {Config} from '@docusaurus/types';
import type * as Preset from '@docusaurus/preset-classic';

const config: Config = {
  title: 'Physical AI & Humanoid Robotics',
  tagline: 'Bridging AI from Digital Brain to Physical Body',
  favicon: 'img/favicon.ico',

  future: {
    v4: true,
  },

  url: 'https://physical-ai-humanoid-robotics-g4ok.vercel.app/',
  baseUrl: '/',
  trailingSlash: false,

  organizationName: 'noorsahar001', 
  projectName: 'Physical-AI-Humanoid-Robotics',

  onBrokenLinks: 'throw',

  i18n: {
    defaultLocale: 'en',
    locales: ['en'],
  },

  presets: [
    [
      'classic',
      {
        docs: {
          sidebarPath: './sidebars.ts',
          editUrl:
            'https://github.com/noorsahar001/Physical-AI-Humanoid-Robotics',
          },
        theme: {
          customCss: './src/css/custom.css',
        },
      } satisfies Preset.Options,
    ],
  ],

  themeConfig: {
    image: 'img/docusaurus-social-card.jpg',
    colorMode: {
      defaultMode: 'dark',
      respectPrefersColorScheme: true,
    },
    navbar: {
      title: 'Physical AI & Humanoid Robotics',
      logo: {
        alt: 'Physical AI Book Logo',
        src: 'img/logo.svg',
      },
      items: [
        {
          type: 'docSidebar',
          sidebarId: 'tutorialSidebar',
          position: 'left',
          label: 'TextBook',
        },
        {
          type: 'doc',
          docId: 'intro',
          label: 'Introduction',
          position: 'left',
        },
        {
          href: 'https://github.com/noorsahar001/Physical-AI-Humanoid-Robotics',
          label: 'GitHub',
          position: 'right',
        },
      ],
    },
    footer: {
      style: 'dark',
      links: [
        {
          title: 'Course',
          items: [
            {label: 'Introduction', to: '/docs/intro'},
          ],
        },
        {
          title: 'Community',
          items: [
            {label: 'Stack Overflow', href: 'https://stackoverflow.com/questions/tagged/docusaurus'},
            {label: 'Discord', href: 'https://discordapp.com/invite/docusaurus'},
            {label: 'X', href: 'https://x.com/docusaurus'},
          ],
        },
        {
          title: 'More',
          items: [
            {label: 'GitHub', href: 'https://github.com/noorsahar001/Physical-AI-Humanoid-Robotics'},
          ],
        },
      ],
      copyright: `Copyright © ${new Date().getFullYear()} Physical AI & Humanoid Robotics. Built with Docusaurus.`,
    },
    prism: {
      theme: prismThemes.github,
      darkTheme: prismThemes.dracula,
    },
  } satisfies Preset.ThemeConfig,
};

export default config;
