import { initializeApp } from "firebase/app";
import { getFirestore, collection, addDoc } from "firebase/firestore";

const firebaseConfig = {
  // Config injected securely via GCP WIF
  projectId: "maroon-medical-opco"
};

const app = initializeApp(firebaseConfig);
const db = getFirestore(app);

export async function logPatientTriage(patientId, acuityLevel) {
  console.log(`[Maroon Medical] Logging triage for Patient ${patientId}`);
  try {
    const docRef = await addDoc(collection(db, "triage_logs"), {
      patientId: patientId,
      acuityLevel: acuityLevel,
      timestamp: new Date()
    });
    console.log("Document written with ID: ", docRef.id);
  } catch (e) {
    console.error("Error adding document: ", e);
  }
}
