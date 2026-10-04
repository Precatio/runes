export interface CarverProfile {
  name: string;
  id: string; // To link to knowledge base
  idealAngle: number;
  idealDepth: number;
  idealAsymmetry: number;
}

export interface AttributionResult {
  carver: string;
  id: string;
  probability: number;
}

const CARVER_PROFILES: CarverProfile[] = [
  { name: "Öpir", id: "ristare-opir", idealAngle: 85, idealDepth: 4.5, idealAsymmetry: 0.8 },
  { name: "Asmund Kåresson", id: "ristare-asmund", idealAngle: 60, idealDepth: 9.0, idealAsymmetry: 0.2 },
  { name: "Fot", id: "ristare-fot", idealAngle: 70, idealDepth: 6.0, idealAsymmetry: 0.3 },
  { name: "Balle", id: "ristare-balle", idealAngle: 75, idealDepth: 5.0, idealAsymmetry: 0.5 },
  { name: "Visäte", id: "ristare-visate", idealAngle: 95, idealDepth: 4.0, idealAsymmetry: 0.4 }
];

export function calculateAttribution(
  vAngle: number,
  depth: number,
  asymmetry: number
): AttributionResult[] {
  
  // Normalization weights to make the dimensions comparable
  // e.g., an angle difference of 10 degrees shouldn't dwarf a depth difference of 2mm
  const weightAngle = 1.0;     // scale 0-180
  const weightDepth = 10.0;    // scale 0-15
  const weightAsymmetry = 50.0; // scale 0-1
  
  const results = CARVER_PROFILES.map(profile => {
    // Euclidean distance in 3D feature space
    const dAngle = (vAngle - profile.idealAngle) * weightAngle;
    const dDepth = (depth - profile.idealDepth) * weightDepth;
    const dAsym = (asymmetry - profile.idealAsymmetry) * weightAsymmetry;
    
    const distance = Math.sqrt(dAngle * dAngle + dDepth * dDepth + dAsym * dAsym);
    
    // Convert distance to a similarity score (closer to 0 distance = higher similarity)
    // using an exponential decay function
    const similarity = Math.exp(-distance / 30);
    
    return {
      carver: profile.name,
      id: profile.id,
      score: similarity
    };
  });
  
  // Normalize scores to percentages summing to ~100%
  const totalScore = results.reduce((sum, res) => sum + res.score, 0);
  
  const finalResults: AttributionResult[] = results.map(res => ({
    carver: res.carver,
    id: res.id,
    probability: (res.score / totalScore) * 100
  }));
  
  // Sort descending by probability
  return finalResults.sort((a, b) => b.probability - a.probability);
}
