## split data

Split files: `csplit -z 2025_mia_dc_1.xml /\/rdf:Description/ '{*}'`

## make all files read on one line

`for file in *.txt; do
  tmp_file=$(mktemp)
  tr '\n' ' ' < "$file" > "$tmp_file"
  mv "$tmp_file" "$file"
done`

## make a random sample

`shuf -zen500 * | xargs -0 gmv -t /500`

To move a sample of 500 files to a new folder

## join them

`for f in *; do (cat "${f}"; echo) >> base_data.txt; done`

## pairwise

> works! https://colab.research.google.com/drive/1P_SwQLU-27HF1zyeGzDbej3LJwu-02Ym?authuser=1#scrollTo=7idxMsn_391r

And `heavy_partition_community_assignments.tsv` is the community assignment for all edges where SM.ratio over 0.5

BUT --- this is at the moment only for a sample of the data.

Full pairwise comparison is likely to take a good few hours to run!

So, I need to do this again with a better sample. There are ~5000 items in the dataset, I suggest 500 (giving 0.5m pairwise matches).