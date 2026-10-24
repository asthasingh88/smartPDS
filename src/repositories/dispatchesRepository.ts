import {
  db,
  isFirebaseConfigured,
  collection,
  getDocs,
  setDoc,
  doc,
  onSnapshot,
  orderBy,
  query,
  handleFirestoreError,
  OperationType,
  Unsubscribe,
} from '../lib/firebase';
import { DispatchRecord } from '../types';
import { INITIAL_DISPATCHES } from '../data/mockData';

const COLLECTION_NAME = 'dispatches';

export const dispatchesRepository = {
  async getAll(): Promise<DispatchRecord[]> {
    if (!isFirebaseConfigured) {
      return INITIAL_DISPATCHES;
    }
    try {
      const q = query(collection(db, COLLECTION_NAME), orderBy('timestamp', 'desc'));
      const snap = await getDocs(q);
      if (snap.empty) {
        await this.seedInitial();
        return INITIAL_DISPATCHES;
      }
      return snap.docs.map((d) => d.data() as DispatchRecord);
    } catch (err) {
      handleFirestoreError(err, OperationType.GET, COLLECTION_NAME);
    }
  },

  subscribe(
    onData: (dispatches: DispatchRecord[]) => void,
    onError?: (err: Error) => void
  ): Unsubscribe {
    if (!isFirebaseConfigured) {
      onData(INITIAL_DISPATCHES);
      return () => {};
    }

    const q = query(collection(db, COLLECTION_NAME), orderBy('timestamp', 'desc'));
    return onSnapshot(
      q,
      (snap) => {
        if (snap.empty) {
          this.seedInitial().catch(console.warn);
          onData(INITIAL_DISPATCHES);
          return;
        }
        const items = snap.docs.map((d) => d.data() as DispatchRecord);
        onData(items);
      },
      (error) => {
        onError?.(error);
        handleFirestoreError(error, OperationType.LIST, COLLECTION_NAME);
      }
    );
  },

  async addDispatch(dispatch: DispatchRecord): Promise<void> {
    if (!isFirebaseConfigured) return;
    try {
      await setDoc(doc(db, COLLECTION_NAME, dispatch.challanNumber), {
        ...dispatch,
        createdAt: new Date().toISOString(),
      });
    } catch (err) {
      handleFirestoreError(err, OperationType.CREATE, `${COLLECTION_NAME}/${dispatch.challanNumber}`);
    }
  },

  async seedInitial(): Promise<void> {
    if (!isFirebaseConfigured) return;
    try {
      for (const d of INITIAL_DISPATCHES) {
        await setDoc(doc(db, COLLECTION_NAME, d.challanNumber), {
          ...d,
          createdAt: new Date().toISOString(),
        }, { merge: true });
      }
      console.log('[SmartPDS]: Initial dispatches seeded into Firestore.');
    } catch (err) {
      console.warn('[SmartPDS]: Dispatch seeding notice:', err);
    }
  },
};
