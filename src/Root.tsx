import React from 'react';
import {Composition} from 'remotion';
import {T1TitleOnMap, t1Defaults} from './templates/T1TitleOnMap';

export const Root: React.FC = () => (
  <>
    <Composition
      id="t1TitleOnMap"
      component={T1TitleOnMap}
      durationInFrames={68}
      fps={30}
      width={720}
      height={1280}
      defaultProps={t1Defaults}
    />
  </>
);
