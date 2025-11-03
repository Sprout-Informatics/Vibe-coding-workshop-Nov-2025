# Install packages
!pip install pyngrok streamlit pydeseq2 anndata

# Import pyngrok and set your ngrok authtoken
from pyngrok import ngrok
import getpass

print("Enter your ngrok authtoken. You can find it on your ngrok dashboard: https://dashboard.ngrok.com/get-started/your-authtoken")
authtoken = getpass.getpass()
ngrok.set_auth_token(authtoken)

# Save the Streamlit app code to a Python file
# We'll use the combined code from the previous steps

streamlit_app_code = """
import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
import base64
from pydeseq2.dds import DeseqDataSet
from pydeseq2.default_inference import DefaultInference
from pydeseq2.ds import DeseqStats
import concurrent.futures
import warnings
import itertools
import logging
import anndata as ad # Import anndata

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Set up the page title and description
st.title("Gene Expression Analysis Dashboard")
st.write("Upload your gene counts and sample information files to perform differential gene expression analysis using DESeq2 and visualize the results with volcano plots.")

# File upload widgets
counts_file = st.file_uploader("Upload Counts File", type=['csv', 'txt'])
sample_info_file = st.file_uploader("Upload Sample Information File (with sample_id and group columns)", type=['csv', 'txt'])

# Conditional block to trigger analysis when both files are uploaded
if counts_file is not None and sample_info_file is not None:
    try:
        # Data loading
        counts_df = pd.read_csv(counts_file, sep=None, engine='python')
        sample_info_df = pd.read_csv(sample_info_file, sep=None, engine='python')

        st.write("Counts data loaded successfully:")
        st.write(counts_df.head())
        st.write("Sample Information data loaded successfully:")
        st.write(sample_info_df.head())

        # Validate sample info file
        if 'sample_id' not in sample_info_df.columns or 'group' not in sample_info_df.columns:
            st.error("Sample Information file must contain 'sample_id' and 'group' columns.")
        else:
            # Set sample_id as index for sample_info_df
            sample_info_df.set_index('sample_id', inplace=True)

            # Align counts_df columns with sample_info_df index
            # Assuming counts_df columns are sample IDs
            counts_df.set_index(counts_df.columns[0], inplace=True) # Assuming gene names are in the first column
            counts_df = counts_df[sample_info_df.index]


            # Get unique conditions and generate all pairwise comparisons
            conditions = sample_info_df['group'].unique()
            if len(conditions) < 2:
                st.error("Sample Information file must contain at least two different groups for comparison.")
            else:
                comparisons_list = list(itertools.combinations(conditions, 2))
                contrasts_df = pd.DataFrame(comparisons_list, columns=['condition_A', 'condition_B'])

                st.write("Generated comparisons:")
                st.write(contrasts_df)

                # Run DESeq2 analysis asynchronously if not already in session state
                if 'deseq2_results' not in st.session_state:
                    st.write("Running DESeq2 analysis for all comparisons...")
                    # Define and call the asynchronous DESeq2 function
                    def run_deseq2_async(counts_df, sample_info_df, contrasts_df):
                        # Runs DESeq2 analysis for each contrast asynchronously.
                        #
                        # Args:
                        #     counts_df: DataFrame with gene counts (rows are genes, columns are samples).
                        #     sample_info_df: DataFrame with sample information (index is sample_id, 'group' column exists).
                        #     contrasts_df: DataFrame defining contrasts (e.g., 'condition_A', 'condition_B' columns).
                        #
                        # Returns:
                        #     A dictionary where keys are comparison names and values are DESeq2 results DataFrames.
                        #
                        results = {}
                        warnings.filterwarnings("ignore", message="Input data counts are not integers.")

                        # Determine the column names for condition A and condition B dynamically
                        if contrasts_df.shape[1] != 2:
                             logging.error("Contrasts file must have exactly two columns.")
                             st.error("Internal Error: Contrasts file must have exactly two columns.")
                             return {}

                        condition_col_a = contrasts_df.columns[0]
                        condition_col_b = contrasts_df.columns[1]


                        def analyze_contrast(row):
                            try:
                                # Use the dynamically determined column names
                                condition_a = row[condition_col_a]
                                condition_b = row[condition_col_b]
                                contrast_name = f"{condition_a}_vs_{condition_b}"
                                logging.info(f"Starting analysis for contrast: {contrast_name}")

                                # Select samples relevant to the current contrast from the sample_info_df
                                relevant_samples_info = sample_info_df[sample_info_df['group'].isin([condition_a, condition_b])]

                                # Select relevant counts based on the sample IDs in relevant_samples_info
                                relevant_counts = counts_df[relevant_samples_info.index]


                                # Ensure sample names are consistent in counts and sample_info
                                relevant_counts = relevant_counts.T.astype(int) # Transpose and ensure integer counts
                                relevant_counts.index.name = 'sample'
                                relevant_counts.columns.name = 'gene'

                                # Create AnnData object
                                adata = ad.AnnData(X=relevant_counts, obs=relevant_samples_info)


                                # Create DeseqDataSet
                                inference_obj = DefaultInference(n_cpus=2) # Adjust n_cpus as needed
                                dds = DeseqDataSet(
                                    adata=adata, # Pass AnnData object
                                    design_factors=["group"], # Design factor is now 'group' from sample_info
                                    # removed refit_dispersions=False,
                                    inference=inference_obj
                                )

                                # Run DESeq2
                                dds.deseq2()

                                # Perform statistical analysis for the contrast
                                stat_res = DeseqStats(dds, contrast=["group", condition_a, condition_b]) # Contrast based on 'group'
                                stat_res.summary()
                                logging.info(f"Completed analysis for contrast: {contrast_name}")

                                return contrast_name, stat_res.results_df
                            except Exception as e:
                                logging.error(f"Error processing contrast {condition_a} vs {condition_b}: {e}", exc_info=True)
                                st.error(f"Error processing contrast {condition_a} vs {condition_b}: {e}")
                                return None, None

                        # Use ThreadPoolExecutor for asynchronous execution
                        with concurrent.futures.ThreadPoolExecutor() as executor:
                            future_to_contrast = {executor.submit(analyze_contrast, contrasts_df.iloc[i]): i for i in range(len(contrasts_df))}
                            for future in concurrent.futures.as_completed(future_to_contrast):
                                contrast_name, result_df = future.result()
                                if contrast_name and result_df is not None:
                                    results[contrast_name] = result_df

                        return results


                    deseq2_results = run_deseq2_async(counts_df.copy(), sample_info_df.copy(), contrasts_df.copy()) # Pass copies

                    if deseq2_results:
                        st.success("DESeq2 analysis completed successfully!")
                        st.session_state['deseq2_results'] = deseq2_results
                        st.write("Available comparisons:")
                        for comparison in deseq2_results.keys():
                            st.write(f"- {comparison}")
                    else:
                        st.warning("DESeq2 analysis completed, but no results were generated.")

    except Exception as e:
        logging.error(f"An error occurred during the data loading or analysis setup: {e}", exc_info=True)
        st.error(f"An error occurred during the data loading or analysis setup: {e}")


# Display comparison selection and results table if results are available
if 'deseq2_results' in st.session_state and st.session_state['deseq2_results']:
    st.subheader("View Differential Gene Expression Results")

    comparisons = list(st.session_state['deseq2_results'].keys())
    selected_comparison = st.selectbox("Select a comparison:", comparisons)

    if selected_comparison:
        selected_results_df = st.session_state['deseq2_results'][selected_comparison]
        st.write(f"Displaying results for: **{selected_comparison}**")
        st.dataframe(selected_results_df) # Display the results table

        # Define the volcano plot generation function
        def generate_volcano_plot(results_df, alpha, color_up, color_down, color_ns, log2fc_threshold, padj_threshold):
            # Generates an interactive volcano plot using Plotly with customization options.
            #
            # Args:
            #     results_df: DataFrame with DESeq2 results for a single comparison.
            #                   Must contain 'log2FoldChange' and 'padj' columns.
            #     alpha: Transparency value for markers.
            #     color_up: Color for upregulated genes.
            #     color_down: Color for downregulated genes.
            #     color_ns: Color for not significant genes.
            #     log2fc_threshold: Log2 fold change threshold for significance.
            #     padj_threshold: Adjusted p-value threshold for significance.
            #
            # Returns:
            #     A Plotly figure object.
            #
            # Handle potential zero padj values before taking logarithm
            results_df['padj_for_plot'] = results_df['padj'].apply(lambda x: x if x is not None and x > 0 else 1e-100)

            # Calculate -log10(padj)
            results_df['-log10(padj)'] = -np.log10(results_df['padj_for_plot'])

            # Categorize genes based on thresholds
            results_df['Regulation'] = 'Not significant'
            results_df.loc[(results_df['log2FoldChange'].abs() >= log2fc_threshold) & (results_df['padj'] <= padj_threshold), 'Regulation'] = \
                results_df['log2FoldChange'].apply(lambda x: 'Upregulated' if x > 0 else 'Downregulated')

            # Define color map based on categories
            color_map = {'Upregulated': color_up, 'Downregulated': color_down, 'Not significant': color_ns}

            # Create the scatter plot
            fig = px.scatter(
                results_df,
                x='log2FoldChange',
                y='-log10(padj)',
                hover_name=results_df.index, # Assuming gene names are in the index
                color='Regulation',
                color_discrete_map=color_map,
                opacity=alpha,
                hover_data={
                    'log2FoldChange': True,
                    'padj': True,
                    '-log10(padj)': False, # Hide the calculated column from hover
                    'Regulation': False # Hide regulation category from hover
                },
                title='Volcano Plot',
                labels={'log2FoldChange': 'Log2 Fold Change', '-log10(padj)': '-log10(Adjusted P-value)'}
            )

            # Customize plot appearance
            fig.update_layout(
                xaxis_title="Log2 Fold Change",
                yaxis_title="-log10(Adjusted P-value)",
                title_x=0.5 # Center the title
            )

            return fig


        # Conditional block to display plot and customization options if results are selected
        if selected_results_df is not None:
            st.subheader("Volcano Plot")

            st.sidebar.subheader("Plot Customization")

            # Add customization widgets to the sidebar
            alpha_value = st.sidebar.slider("Marker Transparency (Alpha)", 0.0, 1.0, 0.7, 0.05)

            st.sidebar.write("Gene Colors:")
            color_upregulated = st.sidebar.color_picker("Upregulated", "#FF0000") # Red
            color_downregulated = st.sidebar.color_picker("Downregulated", "#0000FF") # Blue
            color_not_significant = st.sidebar.color_picker("Not Significant", "#808080") # Gray

            log2fc_thresh = st.sidebar.number_input("Log2 Fold Change Threshold", value=1.0, min_value=0.0, step=0.1)
            padj_thresh = st.sidebar.number_input("Adjusted P-value Threshold", value=0.05, min_value=0.0, max_value=1.0, step=0.01, format="%.3f")

            # Generate the volcano plot with customization parameters
            volcano_fig = generate_volcano_plot(
                selected_results_df.copy(), # Pass a copy
                alpha_value,
                color_upregulated,
                color_downregulated,
                color_not_significant,
                log2fc_thresh,
                padj_thresh
            )
            st.plotly_chart(volcano_fig)

            # Add download button after the plot is displayed
            if volcano_fig is not None:
                # Get HTML representation of the Plotly figure
                volcano_html = volcano_fig.to_html(full_html=True, include_plotlyjs='include')

                # Create a download button
                st.download_button(
                    label="Download Volcano Plot as HTML",
                    data=volcano_html,
                    file_name="volcano_plot.html",
                    mime="text/html"
                )
"""

with open("app.py", "w") as f:
    f.write(streamlit_app_code)

# Run the Streamlit app and tunnel with ngrok
print("Starting Streamlit app...")
public_url = ngrok.connect(addr=8501, proto="http")
print(f"Streamlit app public URL: {public_url}")

!streamlit run app.py --server.port 8501
