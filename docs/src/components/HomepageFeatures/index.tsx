import React from "react";
import clsx from "clsx";
import styles from "./styles.module.css";

type FeatureItem = {
  title: string;
  Svg: React.ComponentType<React.ComponentProps<"svg">>;
  description: JSX.Element;
};

const FeatureList: FeatureItem[] = [
  {
    title: "多适配器集成",
    Svg: require("@site/static/img/undraw_docusaurus_mountain.svg").default,
    description: <>只需要调用SAA，就能向多个平台发送你的消息</>,
  },
  {
    title: "轻松使用",
    Svg: require("@site/static/img/undraw_docusaurus_tree.svg").default,
    description: <>不需要过多学习成本，和Nonebot会话控制一样简单</>,
  },
  {
    title: "基于Nonebot2",
    Svg: require("@site/static/img/undraw_docusaurus_nonebot2.svg").default,
    description: <>跨平台 PYTHON 异步机器人框架</>,
  },
];

function Feature({ title, Svg, description }: FeatureItem) {
  return (
    <div className={clsx("col col--4")}>
      <div className="text--center">
        <Svg className={styles.featureSvg} role="img" />
      </div>
      <div className="text--center padding-horiz--md">
        <h3>{title}</h3>
        <p>{description}</p>
      </div>
    </div>
  );
}

export default function HomepageFeatures(): JSX.Element {
  return (
    <section className={styles.features}>
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
