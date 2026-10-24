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
import { AuditLog } from '../types';
import { INITIAL_AUDIT_LOGS } from '../data/mockData';

const COLLECTION_NAME = 'audit_logs';

export const auditLogsRepository = {
  async getAll(): Promise<AuditLog[]> {
    if (!isFirebaseConfigured) {
      return INITIAL_AUDIT_LOGS;
    }
    try {
      const q = query(collection(db, COLLECTION_NAME), orderBy('timestamp', 'desc'));
      const snap = await getDocs(q);
      if (snap.empty) {
        await this.seedInitial();
        return INITIAL_AUDIT_LOGS;
      }
      return snap.docs.map((d) => d.data() as AuditLog);
    } catch (err) {
      handleFirestoreError(err, OperationType.GET, COLLECTION_NAME);
    }
  },

  subscribe(
    onData: (logs: AuditLog[]) => void,
    onError?: (err: Error) => void
  ): Unsubscribe {
    if (!isFirebaseConfigured) {
      onData(INITIAL_AUDIT_LOGS);
      return () => {};
    }

    const q = query(collection(db, COLLECTION_NAME), orderBy('timestamp', 'desc'));
    return onSnapshot(
      q,
      (snap) => {
        if (snap.empty) {
          this.seedInitial().catch(console.warn);
          onData(INITIAL_AUDIT_LOGS);
          return;
        }
        const items = snap.docs.map((d) => d.data() as AuditLog);
        onData(items);
      },
      (error) => {
        onError?.(error);
        handleFirestoreError(error, OperationType.LIST, COLLECTION_NAME);
      }
    );
  },

  async addLog(log: AuditLog): Promise<void> {
    if (!isFirebaseConfigured) return;
    try {
      await setDoc(doc(db, COLLECTION_NAME, log.id), {
        ...log,
        createdAt: new Date().toISOString(),
      });
    } catch (err) {
      handleFirestoreError(err, OperationType.CREATE, `${COLLECTION_NAME}/${log.id}`);
    }
  },

  async seedInitial(): Promise<void> {
    if (!isFirebaseConfigured) return;
    try {
      for (const log of INITIAL_AUDIT_LOGS) {
        await setDoc(doc(db, COLLECTION_NAME, log.id), {
          ...log,
          createdAt: new Date().toISOString(),
        }, { merge: true });
      }
      console.log('[SmartPDS]: Initial audit logs seeded into Firestore.');
    } catch (err) {
      console.warn('[SmartPDS]: Audit log seeding notice:', err);
    }
  },
};
