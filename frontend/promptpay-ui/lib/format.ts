export function shortTx(tx: string, chars = 6) {
    if (!tx) return "";
    return `${tx.slice(0, chars)}…${tx.slice(-4)}`;
  }
  
  export function arcTxUrl(tx: string) {
    return `https://testnet.arcscan.app/tx/${tx}`;
  }
  
  export function arcAddressUrl(address: string) {
    return `https://testnet.arcscan.app/address/${address}`;
  }
  