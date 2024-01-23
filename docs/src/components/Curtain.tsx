import React from "react";
import "@site/src/css/heimu.css";

const Curtain = ({
  children,
  mutter = "你知道的太多了",
}: {
  children: string;
  mutter?: string;
}) => {
  return (
    <span className="heimu" title={mutter}>
      {children}
    </span>
  );
};

export default Curtain;
