// Kiểm tra: khóa dịch dùng trong code có đủ ở cả vi và en không, và còn emoji nào không
import fs from 'fs';
import path from 'path';
import { translations } from '../src/i18n/translations.js';

const srcDir = path.resolve( 'src' );
const files = [];
function walk( dir ) {
  for ( const name of fs.readdirSync( dir ) ) {
    const full = path.join( dir, name );
    if ( fs.statSync( full ).isDirectory() ) walk( full );
    else if ( /\.(jsx?|css)$/.test( name ) ) files.push( full );
  }
}
walk( srcDir );

const viKeys = new Set( Object.keys( translations.vi ) );
const enKeys = new Set( Object.keys( translations.en ) );
let problems = 0;

// 1. So khớp khóa giữa 2 ngôn ngữ
for ( const k of viKeys ) if ( !enKeys.has( k ) ) { console.log( 'THIEU EN:', k ); problems++; }
for ( const k of enKeys ) if ( !viKeys.has( k ) ) { console.log( 'THIEU VI:', k ); problems++; }

// 2. Khóa cố định được gọi bằng t( '...' )
const used = new Set();
const dynamicPrefixes = [ 'status.', 'type.', 'movement.', 'action.', 'error.' ];
for ( const f of files.filter( ( x ) => x.endsWith( '.jsx' ) ) ) {
  const text = fs.readFileSync( f, 'utf8' );
  for ( const m of text.matchAll( /\bt\(\s*['"`]([^'"`$]+)['"`]/g ) ) used.add( m[ 1 ] );
}
for ( const k of used ) {
  if ( dynamicPrefixes.some( ( p ) => k === p ) ) continue;
  if ( !viKeys.has( k ) ) { console.log( 'KHOA KHONG TON TAI:', k ); problems++; }
}

// 3. Emoji còn sót
const emojiRegex = /[\u{1F300}-\u{1FAFF}\u{2600}-\u{27BF}\u{2B50}\u{23F0}-\u{23F3}\u{FE0F}]/u;
for ( const f of files ) {
  fs.readFileSync( f, 'utf8' ).split( '\n' ).forEach( ( line, i ) => {
    if ( emojiRegex.test( line ) ) { console.log( 'EMOJI:', path.relative( srcDir, f ), i + 1, line.trim().slice( 0, 60 ) ); problems++; }
  } );
}

console.log( problems === 0 ? 'OK: khong co van de' : `Co ${ problems } van de` );
