# phidata/pipeline.py

from phidata import App
from phidata.pipeline import Pipeline, Step

# The name of the image you built (e.g., pitchperfect:latest)
CONTAINER_IMAGE = "pitchperfect:latest"

# Step: Run your main script inside the container
main_step = Step(
    name="run-pitchperfect",
    image=CONTAINER_IMAGE,
    command=["python", "main.py"],
    env={"OPENAI_API_KEY": "{{ env.OPENAI_API_KEY }}"},
)

# Define a pipeline with one step
my_pipeline = Pipeline(name="pitchperfect-pipeline", steps=[main_step])

# Create an App that references the pipeline
app = App(name="pitchperfect-app", pipelines=[my_pipeline])
