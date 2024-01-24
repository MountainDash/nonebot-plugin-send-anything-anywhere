import React from "react";

/**
 * 在被包围元素的右上角添加一个小圆点
 */
const DotMark = ({
  children,
  color,
}: {
  children: React.ReactNode;
  color: string;
}) => {
  return (
    <div style={{ position: "relative", display: "inline-block" }}>
      {children}
      <div
        style={{
          position: "absolute",
          top: "0px",
          right: "-10px",
          width: "8px",
          height: "8px",
          borderRadius: "50%",
          backgroundColor: color,
        }}
      ></div>
    </div>
  );
};

export default DotMark;
