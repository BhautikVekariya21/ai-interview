const DB_NAME = "interviewer_db";
const STORE_NAME = "keyval";
const DB_VERSION = 1;

type MemoryStore = Map<string, unknown>;

let memoryFallback: MemoryStore | null = null;

function getMemoryStore(): MemoryStore {
  if (!memoryFallback) memoryFallback = new Map();
  return memoryFallback;
}

function hasIndexedDB(): boolean {
  return typeof window !== "undefined" && "indexedDB" in window && window.indexedDB != null;
}

function openDB(): Promise<IDBDatabase> {
  return new Promise((resolve, reject) => {
    const request = window.indexedDB.open(DB_NAME, DB_VERSION);
    request.onupgradeneeded = () => {
      const db = request.result;
      if (!db.objectStoreNames.contains(STORE_NAME)) {
        db.createObjectStore(STORE_NAME);
      }
    };
    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error);
  });
}

async function withStore<T>(
  mode: IDBTransactionMode,
  run: (store: IDBObjectStore) => IDBRequest,
): Promise<T> {
  const db = await openDB();
  return new Promise<T>((resolve, reject) => {
    const tx = db.transaction(STORE_NAME, mode);
    const store = tx.objectStore(STORE_NAME);
    const request = run(store);
    request.onsuccess = () => resolve(request.result as T);
    request.onerror = () => reject(request.error);
    tx.oncomplete = () => db.close();
  });
}

export async function getItem<T>(key: string): Promise<T | null> {
  if (!hasIndexedDB()) {
    return (getMemoryStore().get(key) as T) ?? null;
  }
  try {
    const value = await withStore<T | undefined>("readonly", (store) => store.get(key));
    return value ?? null;
  } catch {
    return (getMemoryStore().get(key) as T) ?? null;
  }
}

export async function setItem<T>(key: string, value: T): Promise<void> {
  if (!hasIndexedDB()) {
    getMemoryStore().set(key, value);
    return;
  }
  try {
    await withStore("readwrite", (store) => store.put(value as unknown, key));
  } catch {
    getMemoryStore().set(key, value);
  }
}

export async function removeItem(key: string): Promise<void> {
  if (!hasIndexedDB()) {
    getMemoryStore().delete(key);
    return;
  }
  try {
    await withStore("readwrite", (store) => store.delete(key));
  } catch {
    getMemoryStore().delete(key);
  }
}
