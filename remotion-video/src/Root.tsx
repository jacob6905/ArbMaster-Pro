import React from "react";
import { Composition } from "remotion";
import { RailgunVideo } from "./components/RailgunVideo";

// Video configuration
// 12 seconds at 30fps = 360 frames
const FPS = 30;
const DURATION_SECONDS = 12;
const DURATION_FRAMES = FPS * DURATION_SECONDS;

export const RemotionRoot: React.FC = () => {
  return (
    <>
      <Composition
        id="RailgunVideo"
        component={RailgunVideo}
        durationInFrames={DURATION_FRAMES}
        fps={FPS}
        width={1920}
        height={1080}
        defaultProps={{}}
      />

      {/* Alternative shorter version - 10 seconds */}
      <Composition
        id="RailgunVideoShort"
        component={RailgunVideo}
        durationInFrames={FPS * 10}
        fps={FPS}
        width={1920}
        height={1080}
        defaultProps={{}}
      />

      {/* Square format for social media */}
      <Composition
        id="RailgunVideoSquare"
        component={RailgunVideo}
        durationInFrames={DURATION_FRAMES}
        fps={FPS}
        width={1080}
        height={1080}
        defaultProps={{}}
      />
    </>
  );
};
