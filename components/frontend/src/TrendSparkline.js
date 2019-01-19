import React from 'react';
import { VictoryGroup, VictoryLine, VictoryTheme } from 'victory';


function TrendSparkline(props) {
  let measurements = [];
  let targets = [];
  for (var i = 0; i < props.measurements.length; i++) {
    const measurement = props.measurements[i].measurement;
    const m = measurement.measurement !== null ? Number(measurement.measurement) : null;
    const t = Number(measurement.target);
    const x1 = new Date(measurement.start);
    const x2 = new Date(measurement.end);
    measurements.push({y: m, x: x1});
    measurements.push({y: m, x: x2});
    targets.push({y: t, x: x1});
    targets.push({y: t, x: x2});
  }
  return (
    <VictoryGroup theme={VictoryTheme.material} scale={{ x: "time", y: "linear" }} height={60} padding={0}>
      <VictoryLine data={measurements} interpolation="stepBefore" style={{
        data: {
          stroke: "black", strokeWidth: 3
        }
      }}/>
      <VictoryLine data={targets} style={{
        data: {
          stroke: "green", strokeWidth: 3, strokeDasharray: "3 3"
        }
      }}/>
    </VictoryGroup>
  )
}


export { TrendSparkline };