# Unsupervised Pretraining Improves Natural Language Model Performance in a Client-Centric Service Model: A Case Study


## Abstract
Recent advancements in natural language processing techniques enable unsupervised learning of unlabeled corpora to construct models exhibiting state-of-the-art performance. Corporations with a customer-centric service-based model can leverage these techniques to build models pretrained on client facing materials. These models can be fine-tuned to deliver novel client-facing products or achieve greater efficiency on client-centric internal processes. In this paper, I pretrain bidirectional encoder representations from transformers (BERT) on a set of research document products. The transformers are embedded into a traditional categorization model to classify client service requests for routing to the appropriate consultants for the request topic. The models show modest improvements in performance compared to a baseline BERT model without pretraining. This project operates as a case study on the common obstacles faced in a corporate, low-resource environment, and the results are a proof-of-concept for future investment in unsupervised learning of natural language in service-based business models.

## Code Files
0. project_utilities.py
1. Data preprocessing
	* research_doc_preprocessing.py
	* foundational_doc_scraping.py
	* document_sentence_split.py
2. BERT Model Pretraining
	* domain_vocab_update.py
3. BERT Model Finetuning
	* data_creation.py

## Results
Model Performance by Evaluation Metric

**Pretraining Evaluation: Masked Language Model Accuracy by Training Steps / Warm-up Steps**
| Model       |  20/10  |  100/20  |  10,000/100  |   0/0 (base)  |
| ------------|:-------:|:--------:|:------------:|:-------------:|
| BERT-Tiny   | 28.25%	|  29.83%  | 	39.15%    |    28.36%     |
| BERT-Mini   | 43.55%	|  46.45%  |	59.54%    |    42.87%     |
| BERT-Medium | 54.07%	|  59.51%  |	81.27%    |    53.87%     |


**Pretraining Evaluation: Next Sentence Accuracy by Training Steps / Warm-up Steps**
| Model       |  20/10  |  100/20  |  10,000/100  |   0/0 (base)  |
| ------------|:-------:|:--------:|:------------:|:-------------:|
| BERT-Tiny   | 76.00%	|  80.00%  | 	86.13%    |    52.50%     |
| BERT-Mini   | 87.13%	|  90.63%  |	99.25%    |    54.63%     |
| BERT-Medium | 87.63%	|  95.50%  |	100.00%   |    56.88%     |


**Fine-tuning Evaluation: Classification Accuracy by Training Steps / Warm-up Steps**
| Model       |  20/10  |  100/20  |  10,000/100  |   0/0 (base)  |
| ------------|:-------:|:--------:|:------------:|:-------------:|
| BERT-Tiny   | 54.53%	|  52.16%  | 	52.89%    |    51.25%     |
| BERT-Mini   | 66.08%	|  65.35%  |	65.71%    |    66.32%     |
| BERT-Medium | 68.02%	|  67.72%  |	68.57%    |    67.78%     |
