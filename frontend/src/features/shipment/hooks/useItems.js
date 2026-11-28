import { useCallback, useEffect, useState } from 'react';
import { useShipment } from '../context/ShipmentContext';

/** Item catalogue from Inventory. If Inventory does not answer, item ids are shown. */
export function useItems() {
  const { inventory } = useShipment();
  const [items, setItems] = useState([]);

  useEffect(() => {
    inventory.listItems().then(setItems).catch(() => setItems([]));
  }, [inventory]);

  const nameOf = useCallback(
    (id) => items.find((item) => item.id === id)?.name ?? `Mặt hàng #${id}`,
    [items],
  );
  return { items, nameOf };
}
