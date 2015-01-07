import random, sys, os
import numpy as np
sys.path.append(os.path.expanduser('~/git/time_freq_auditory_scene/'))

from TimeFreqAuditoryScene import *
from Chambers import *

# This is a pychoacoustics implementation of the standard paradigm of Chambers and Pressnitzer 2014



DELAY_CTX_TRITONE = "Delay Context <-> Tritone (s)"
DELAY_INTER_TRIAL = "Delay trial_{i} <-> trial_{i+1} (s)"
LEVEL = "Level (dB SPL)"
SPEC_ENV_MEAN = "Spectral Envelope: mean (Hz)"
SPEC_ENV_STD ="Spectral Envelope: std (octave)"
NB_TONES_CLR = "#Tones in clearing stimulus (int)"
DELAY_CLR_CTX = "Delay Clearing <-> Context (s)"
DURATION_TONE_CLR = "Duration tone in clearing (s)"
DURATION_SP_CTX = "Duration SP in context (s)"
DELAY_SP_CONTEXT = "Delay SP <-> SP in context (s)"
NB_SP_CTX = "#SP in context (int)"
DURATION_SP_TRT = "Duration SP in tritone (s)"
DELAY_SP_TRT = "Delay SP <-> SP in tritone (s)"
RAMPS = "Ramps (s)"

def initialize_context_bias(prm):
    """
    set some general parameters and options for the experiment
    :return:
    """
    exp_name = "Contextual Bias Tritone (classical)"
    prm["experimentsChoices"].append(exp_name)
    prm[exp_name] = {}

    # paradigm: Constant 1-Interval 2-Alternatives
    # This paradigm implements a constant difference method for tasks
    # with a single observation interval and two response alternatives,
    # such as the “Yes/No” signal detection task.


    prm[exp_name]["paradigmChoices"] = ["Constant 1-Interval 2-Alternatives"]  # 1 stimulus, 2 choices
    prm[exp_name]["opts"] = ["hasFeedback"]

    prm[exp_name]["buttonLabels"] = ["Up", "Down"]
    prm[exp_name]['defaultNIntervals'] = 1
    prm[exp_name]['defaultNAlternatives'] = 2
    prm[exp_name]["execString"] = "context_bias"
    prm[exp_name]["version"] = "1"

    return prm


def select_default_parameters_context_bias(parent, par):
    """
    lists all the widgets (text fields and choosers) of the experiment and their default values
    :return:
    """

    field = []
    fieldLabel = []
    chooser = []
    chooserLabel = []
    chooserOptions = []

    # ===============================
    # Parameterization of experiment
    # ===============================
    # --------- Global
    # - delay context <-> tritone
    # - delay trial_{i} <-> trial_{i+1}
    # - loudness: 64dB SPL
    # - spectral envelope:mu_log
    # - spectral envelope:sigma_log
    # --------- Clear
    # - #tones in clearing stimulus
    # - delay clearing <-> context
    # --------- Context
    # - duration SP in context
    # - delay SP <-> SP in context
    # - #SP in context
    # --------- Tritone
    # - duration SP in tritone
    # - delay SP <-> SP in tritone



    fieldLabel.append(DELAY_CTX_TRITONE)
    field.append(0.2)
    fieldLabel.append(DELAY_INTER_TRIAL)
    field.append(1)
    fieldLabel.append(LEVEL)
    field.append(64)
    fieldLabel.append(SPEC_ENV_MEAN)
    field.append(300.)
    fieldLabel.append(SPEC_ENV_STD)
    field.append(2.)

    fieldLabel.append(NB_TONES_CLR)
    field.append(3)
    fieldLabel.append(DELAY_CLR_CTX)
    field.append(0.5)
    fieldLabel.append(DURATION_TONE_CLR)
    field.append(0.2)

    fieldLabel.append(DURATION_SP_CTX)
    field.append(0.2)
    fieldLabel.append(DELAY_SP_CONTEXT)
    field.append(0.01)
    fieldLabel.append(NB_SP_CTX)
    field.append(5)

    fieldLabel.append(DURATION_SP_TRT)
    field.append(0.2)
    fieldLabel.append(DELAY_SP_TRT)
    field.append(0.01)

    fieldLabel.append(RAMPS)
    field.append(0.01)

    chooserOptions.append([parent.tr("Right"), parent.tr("Left"), parent.tr("Both")])
    chooserLabel.append(parent.tr("Channel:"))
    chooser.append(parent.tr("Both"))

    prm = {}
    prm['field'] = field
    prm['fieldLabel'] = fieldLabel
    prm['chooser'] = chooser
    prm['chooserLabel'] = chooserLabel
    prm['chooserOptions'] = chooserOptions

    return prm


def doTrial_context_bias(parent):
    """
    code that generates the sounds and plays them during the experiment
    :return:
    """
    currBlock = 'b'+ str(parent.prm['currentBlock'])  # get current block from context
    if parent.prm['startOfBlock'] == True:
        parent.writeResultsHeader('log')

    # For experiments using the “Constant 1-Interval 2-Alternatives” paradigm
    # it is necessary to list the experimental conditions
    parent.prm['conditions'] = ["Up", "Down"]
    condition = random.choice(parent.prm['conditions'])
    parent.currentCondition = condition
    if parent.currentCondition == 'Up':
        parent.correctButton = 1
    elif parent.currentCondition == 'Down':
        parent.correctButton = 2

    print(condition)


    # --------------- getting parameters from context

    delay_ctx_tritone = \
        parent.prm[currBlock]['field'][parent.prm['fieldLabel'].index(DELAY_CTX_TRITONE)]
    delay_inter_trial = \
        parent.prm[currBlock]['field'][parent.prm['fieldLabel'].index(DELAY_INTER_TRIAL)]
    level = \
        parent.prm[currBlock]['field'][parent.prm['fieldLabel'].index(LEVEL)]
    spec_env_mean = \
        parent.prm[currBlock]['field'][parent.prm['fieldLabel'].index(SPEC_ENV_MEAN)]
    spec_env_std = \
        parent.prm[currBlock]['field'][parent.prm['fieldLabel'].index(SPEC_ENV_STD)]
    nb_tones_clear = int(\
        parent.prm[currBlock]['field'][parent.prm['fieldLabel'].index(NB_TONES_CLR)])
    delay_clear_ctx = \
        parent.prm[currBlock]['field'][parent.prm['fieldLabel'].index(DELAY_CLR_CTX)]
    duration_tone_clr = \
        parent.prm[currBlock]['field'][parent.prm['fieldLabel'].index(DURATION_TONE_CLR)]
    duration_sp_ctx = \
        parent.prm[currBlock]['field'][parent.prm['fieldLabel'].index(DURATION_SP_CTX)]
    delay_inter_sp_ctx = \
        parent.prm[currBlock]['field'][parent.prm['fieldLabel'].index(DELAY_SP_CONTEXT)]
    nb_sp_ctx = int(\
        parent.prm[currBlock]['field'][parent.prm['fieldLabel'].index(NB_SP_CTX)])
    duration_sp_trt = \
        parent.prm[currBlock]['field'][parent.prm['fieldLabel'].index(DURATION_SP_TRT)]
    delay_inter_sp_trt = \
        parent.prm[currBlock]['field'][parent.prm['fieldLabel'].index(DELAY_SP_TRT)]
    ramps = \
        parent.prm[currBlock]['field'][parent.prm['fieldLabel'].index(RAMPS)]
    #channel = \
    #    parent.prm[currBlock]['chooser'][parent.prm['chooserLabel'].index("Ear:")]

    # --------------- design your stimulus

    # need to design the stimulus and output a list of 2D np-arrays

    # Global parameters
    fs = parent.prm['sampRate']

    # Shepard tones tritone
    sp_st = 12*np.random.rand()  #int(np.random.randint(12))
    fb1 = 2.**(sp_st/12.)  # base frequency chosen randomly uniformly on log-octave range
    # declare gaussian envelope on log frequency
    genv = GaussianSpectralEnvelope(mu=spec_env_mean, sigma_oct=spec_env_std)

    # ===================================================
    # Scene construction
    scene = Scene()
    run_time = 0

    clearing = Clearing(n_tones=nb_tones_clear,
                    tone_duration=duration_tone_clr,
                    inter_tone_interval=delay_inter_sp_ctx,
                    env=genv,
                    delay=run_time,
                    ramps=ramps)

    run_time += clearing.getduration() + delay_clear_ctx

    context = Context(n_tones=nb_sp_ctx,
                    tone_duration=duration_sp_ctx,
                    inter_tone_interval=delay_inter_sp_ctx,
                    env=genv,
                    fb_T1=fb1,
                    range_st=[1,5],
                    type="chords",  # chords or streams
                    bias=condition,
                    delay=run_time)

    run_time += context.getduration() + delay_ctx_tritone
    tritone = Tritone(fb=fb1,
                      env=genv,
                      delay=run_time,
                      duration_sp=duration_sp_trt,
                      delay_sp=delay_inter_sp_trt)

    scene.List = [clearing ,context, tritone]

    # ===================================================
    # Constructing the clearing stimulus
    #clearing = []
    #st_clear = []
    #for i in range(nb_tones_clear):
    #    st = range_context[0]+np.random.rand()*(range_context[1]-range_context[0])
    #    st_clear.append(float(st))
    #    tmp_st = ConstantIntervalChord(fb=fb1*2.**(st/12.),interval=np.sqrt(2.), env=genv, delay=run_time, duration=duration_tone_clr)
    #    run_time += duration_tone_clr + delay_inter_sp_ctx
    #    clearing.append(tmp_st)
    # ===================================================
    # Constructing the context
    #run_time += delay_clear_ctx
    #context = []
    #st_ctx = []
    #for i in range(nb_sp_ctx):
    #    st = np.random.rand()*12
    #    st_ctx.append(float(st))
    #    tmp_st = ShepardTone(fb=fb1*2.**(st/12.), env=genv, delay=run_time, duration=duration_sp_ctx)
    #    run_time += duration_sp_ctx + delay_inter_sp_ctx
    #    context.append(tmp_st)
    # ===================================================
    # constructing the tritone
    #run_time += delay_ctx_tritone
    #tritone = Tritone(fb=fb1, env=genv, delay=run_time, duration_sp=duration_sp_trt, delay_sp=delay_inter_sp_trt)
    #scene.List = clearing + context + [tritone]

    # ===================================================
    # generate sound
    print('fs:'+str(fs))
    x = scene.generate(fs=fs)
    # 1D np.ndarray -> 2D np.ndarray (for binaural signal)
    xe = np.vstack([x, x]).T
    print(xe.shape)
    maxLevel = parent.prm['maxLevel']
    amp = 10**((level - maxLevel) / 20.)

    xe *= amp
    #plt.plot(xe)
    #plt.show()

    # additionally saving
    # - base freq of T1
    # - base freq of clearing
    # - base freq of context
    # parent.prm['additional_parameters_to_write'] = [sp_st,st_clear,st_ctx]

    parent.playSequentialIntervals([xe])


