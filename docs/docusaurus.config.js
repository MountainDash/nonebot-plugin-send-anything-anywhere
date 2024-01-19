// @ts-check
// Note: type annotations allow type checking and IDEs autocompletion
const { themes } = require("prism-react-renderer");
const lightCodeTheme = themes.github;
const darkCodeTheme = themes.dracula;

/** @type {import('@docusaurus/types').Config} */
const config = {
  title: "峯驰物流",
  tagline: "Send Anything Anywhere",
  favicon: "img/favicon.ico",

  // Set the production url of your site here
  url: "https://your-docusaurus-test-site.com",
  // Set the /<baseUrl>/ pathname under which your site is served
  // For GitHub pages deployment, it is often '/<projectName>/'
  baseUrl: "/",

  // GitHub pages deployment config.
  // If you aren't using GitHub pages, you don't need these.
  organizationName: "felinea98", // Usually your GitHub org/user name.
  projectName: "nonebot-plugin-send-anything-anywhere", // Usually your repo name.

  onBrokenLinks: "throw",
  onBrokenMarkdownLinks: "warn",

  // Even if you don't use internalization, you can use this field to set useful
  // metadata like html lang. For example, if your site is Chinese, you may want
  // to replace "en" with "zh-Hans".
  i18n: {
    defaultLocale: "zh-Hans",
    locales: ["zh-Hans"],
  },

  presets: [
    [
      "classic",
      /** @type {import('@docusaurus/preset-classic').Options} */
      ({
        docs: {
          sidebarPath: require.resolve("./sidebars.js"),
          routeBasePath: "/",
          // Please change this to your repo.
          // Remove this to remove the "edit this page" links.
          editUrl:
            "https://github.com/felinae98/nonebot-plugin-send-anything-anywhere/docs",
        },
        blog: false,
        theme: {
          customCss: require.resolve("./src/css/custom.css"),
        },
      }),
    ],
  ],

  themeConfig:
    /** @type {import('@docusaurus/preset-classic').ThemeConfig} */
    ({
      // Replace with your project's social card
      colorMode: {
        defaultMode: "dark",
      },
      logo: {
        alt: "Saa Logo",
        src: "img/logo.svg",
        href: "/",
        target: "_self",
      },
      navbar: {
        title: "峯驰物流",
        // logo: {
        //   alt: 'Saa Logo',
        //   src: 'img/logo.svg',
        // },
        hideOnScroll: true,
        items: [
          {
            type: "docSidebar",
            sidebarId: "usageSidebar",
            position: "left",
            label: "使用",
          },
          {
            type: "docSidebar",
            sidebarId: "devSidebar",
            position: "left",
            label: "开发",
          },
          {
            href: "https://github.com/felinae98/nonebot-plugin-send-anything-anywhere",
            label: "GitHub",
            position: "right",
          },
        ],
      },
      docs: {
        sidebar: {
          hideable: true,
          autoCollapseCategories: true,
        },
      },
      footer: {
        style: "dark",
        copyright: `Copyright © ${new Date().getFullYear()} Felinae98. All rights reserved.`,
        links: [
          {
            title: "文档",
            items: [
              {
                label: "使用",
                to: "/usage",
              },
              {
                label: "开发",
                to: "/dev",
              },
            ],
          },
          {
            title: "相关",
            items: [
              {
                label: "Homepage",
                href: "/",
              },
              {
                label: "Q群",
                href: "https://qm.qq.com/cgi-bin/qm/qr?k=pXYMGB_e8b6so3QTqgeV6lkKDtEeYE4f&jump_from=webapi",
              },
            ],
          },
          {
            title: "更多",
            items: [
              {
                label: "Nonebot Bison",
                href: "https://github.com/felinae98/nonebot-bison",
              },
              {
                label: "Docusaurus",
                href: "https://github.com/facebook/docusaurus",
              },
            ],
          },
        ],
      },
      prism: {
        theme: lightCodeTheme,
        darkTheme: darkCodeTheme,
        additionalLanguages: ["python", "bash", "diff", "json"],
      },
    }),
};

module.exports = config;
