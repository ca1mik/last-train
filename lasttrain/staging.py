"""Deterministic, pausable blocking for the final assisted crossing."""
from dataclasses import dataclass

@dataclass
class CrossingSequence:
    elapsed: float = 0.0
    duration: float = 18.0

    def advance(self,dt):
        self.elapsed=min(self.duration,self.elapsed+max(0,dt))
        return self.elapsed>=self.duration

    def actors(self):
        # Lida and Artem share one pace around the stretcher. Pavel leaves last.
        cast=(('nina',0,0,435),('lida',1.8,70,480),
              ('carry_patient',1.8,0,480),('artem',1.8,-70,480),('pavel',4,-100,500))
        result=[]
        for kind,delay,offset,y in cast:
            distance=max(0,min(1110,(self.elapsed-delay)*100))
            x=190+distance+offset
            moving=delay<self.elapsed<delay+11.1
            result.append((kind,(x,y),distance,moving))
        # Healthy residents crossed first; Raisa waits at the far landing.
        result.append(('raisa',(1420,440),0,False))
        return result
