# full2.sh MODEL_IN TAG : build with hand-made textures (no photo projection), render matched view, compose, boards
set -e
cd "$(dirname "$0")"
bash run2.sh $1 $2.png
python board.py $2
