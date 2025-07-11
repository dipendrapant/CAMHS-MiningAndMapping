DB_NAME="*****"
DB_USER="*****"
OUTPUT_DIR="/P4_V5/data/extract" 
if ((BASH_VERSINFO[0] < 4)); then
  echo "Error: this script requires bash version 4 or higher." >&2
  exit 1
fi

declare -A COLS=(
  [pasient]="nr, fdt, morfdt, farfdt, morrelasj, farrelasj, etniskmor, etniskfar, hjemmesprk"
  [sak]="pasient, nr, kjonn, icd1, icd2, icd3, icd4, icd5, icd6, henvdato, igangdato, avsldato"
  [forordning]="pasientnr, preparatid, saknr"
  [resept]="forordningnr, preparatid"
  [preparat]="id, atckode, atcnavn"
  [diagnose]="pasient, sak, opphold, diagnose, akse, dato, hoved"
  [opphold]="nr, pasient, sak, igangdato, avsldato"
  [journal]="nr, type, sak, pasient, opphold"
)
TABLES=(pasient sak forordning resept preparat diagnose opphold journal)
mkdir -p "$OUTPUT_DIR"
for TABLE in "${TABLES[@]}"; do
  OUTFILE="$OUTPUT_DIR/$TABLE.csv"
  COLUMNS="${COLS[$TABLE]}"

  echo "Exporting $TABLE → $OUTFILE (columns: $COLUMNS)"
  psql -U "$DB_USER" -d "$DB_NAME" \
    -c "\copy (
           SELECT $COLUMNS
           FROM public.$TABLE
         ) TO '$OUTFILE' CSV HEADER"
done

echo "All specified columns from each table have been exported to $OUTPUT_DIR."
