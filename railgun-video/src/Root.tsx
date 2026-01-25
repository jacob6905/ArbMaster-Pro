import { Composition } from "remotion";
import { RailgunVideo } from "./RailgunVideo";

export const RemotionRoot: React.FC = () => {
  return (
    <>
      <Composition
        id="RailgunPrivacy"
        component={RailgunVideo}
        durationInFrames={300}
        fps={30}
        width={1920}
        height={1080}
      />
    </>
  );
};
