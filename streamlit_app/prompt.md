Let’s plan to build a gene expression analysis dashboard in python using streamlit
<features>
- Allow the user to input a file with samples and gene counts as features
- Allow the user to input a file with available contrasts
- When the user submits the counts file and contrasts file, an asynchronous process runs deseq2 using the pydesq2 library, comparing each experimental condition against each other condition 
- Once complete, the user can view the available comparison differential gene expression results using a volcano plot
- Allow the user to manipulate plot characteristics, eg, alpha value, color scheme, log2 fold change threshold, p-value threshold, etc
- Give the user the option to download the volcano plot as an html file
</features>

<details>
- The contrast file should have at least two columns: sample_id and group
- The groups in the contrast file group column represent experimental conditions
- Be sure to give the user plenty of verbose logging to track progress and make debugging easier, especially for asynchronous processes
</details>


