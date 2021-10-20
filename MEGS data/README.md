1.) Load and prepare MEGS dataset
-git clone https://github.com/german-asr/megs
-common-voice corpus has to be downloaded manually and placed inside data/download/common_voice
-run recreate.sh in /megs to download and merge all single german audio datasets

2.) Convert MEGS dataset to LibrispeechFormat so it is compatible with RETURNN
- in megs/data/full_waverized run megsformat_to_librispeechformat.py

3.) Load and modify RETURNN so it can be trained on the MEGS Corpus
- in megs/data/full_waverized/librispeechformat git clone https://github.com/rwth-i6/returnn
- extend megs/data/full_waverized/librispeechformat/returnn/GeneratingDataset.py with "MEGSCorpus" Class from 
  GeneratingDataset_megs_corpus_addition.py
- if you want to enable local inference: (Not needed for traning) extend megs/data/full_waverized/librispeechformat/returnn/TFEngine.py
  with "inference" method from TFEngine_local_inference_addition.py

4.) Prepare MEGSCorpus for Training
- run split.py to split in train dev and test from /megs/data/full_waverized/librispeechformat
- run 02_git_clone_subword_nmt.sh in /megs/data/full_waverized/librispeechformat
- copy collect-megs-train-text.py to /megs/data/full_waverized/librispeechformat
  and run 15_create_megs_bpe.sh in /megs/data/full_waverized/librispeechformat
- run 16_create_megs_feature_norm_stats.sh from /megs/data/full_waverized/librispeechformat
- run 17_create_trans_raw.sh from /megs/data/full_waverized/librispeechformat
- run 21_prepare_train.sh from /megs/data/full_waverized/librispeechformat
5.) Train
- copy returnn.config to /megs/data/full_waverized/librispeechformat
- run 22_train.sh from /megs/data/full_waverized/librispeechformat
6.) Infere
- Copy Inference.py to /megs/data/full_waverized/librispeechformat/returnn
- run python Inference.py "example.wav" from /megs/data/full_waverized/librispeechformat/returnn

todo: how to copy language model and encoder-decoder model, How RASR is used
